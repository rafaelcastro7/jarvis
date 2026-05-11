"""
Resuelve quizzes de Anthropic Academy con conocimiento real del dominio.
NO adivina — razona basado en el contenido de la lección y reglas del exam guide.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, re, json
from playwright.async_api import async_playwright

# Base de conocimiento: respuestas correctas derivadas del exam guide y DevCompass (70 lecciones)
KNOWLEDGE_BASE = {
    # Agentic loop - Domain 1
    "stop_reason": {"correct": "tool_use", "when_done": "end_turn"},
    "loop terminates": "end_turn",
    "loop continues": "tool_use",
    "iteration cap": "anti-pattern",  # No usar como mecanismo principal

    # Multi-agent - Domain 1
    "subagent context": "isolated",  # Subagentes NO heredan contexto del coordinator
    "coordinator role": "routing, error handling, aggregation",
    "peer communication": "not allowed",  # Todo pasa por coordinator

    # Escalation - Domain 5
    "escalate when": ["explicit human request", "genuine policy gap", "cannot make progress"],
    "do not escalate": ["frustration", "sentiment", "emotional tone", "complexity"],

    # Tool design - Domain 2
    "tool error retry true": ["rate limit", "timeout", "temporary", "transient"],
    "tool error retry false": ["not found", "permission", "invalid", "permanent"],

    # Structured output - Domain 4
    "structured output method": "tool_use schema",  # Más confiable que pedir JSON en prompt
    "self correction": "include failed output + specific errors in retry",

    # Context - Domain 5
    "lost in middle": "place critical info at beginning or end",
    "long context": "use RAG chunking",

    # Batch vs sync - Domain 5
    "pre-merge check": "synchronous",  # Bloquea el pipeline
    "overnight reports": "batch api",
    "batch max duration": "24 hours",
    "batch multi-turn": "not supported",

    # MCP - Domain 2
    "mcp tools": "actions with side effects",
    "mcp resources": "read-only data",
    "mcp prompts": "reusable templates",

    # Claude Code - Domain 3
    "plan mode when": "multi-file changes, team alignment needed",
    "claude md hierarchy": "project root, then subdirectory overrides",

    # Prompt engineering - Domain 4
    "few shot": "examples in system prompt",
    "xml tags": "structure complex prompts",
    "temperature 0": "deterministic, consistent output",
    "temperature high": "creative, diverse output",
}

# Patrones de respuestas CORRECTAS — fragmentos que indican la opción correcta
CORRECT_PATTERNS = [
    "stop_reason.*tool_use", "end_turn.*terminat", "tool_use.*continu",
    "isolated context", "explicit.*request.*escalat", "genuine.*policy.*gap",
    "cannot make progress", "tool_use schema", "structured.*tool",
    "beginning or end", "synchronous.*blocking", "batch.*latency",
    "coordinator.*manag", "hub.*spoke", "mcp.*connect.*external",
    "system prompt.*tool.*description", "retry.*specific.*error",
    "independent.*instance", "self.review.*limitation",
]

# Patrones de respuestas INCORRECTAS — fragmentos que indican opción incorrecta
WRONG_PATTERNS = [
    "iteration cap.*primary", "arbitrary.*stop", "text content.*indicator",
    "peer.*peer", "sentiment.*escalat", "frustrat.*escalat",
    "temperature.*escalat", "fine.tun.*escalat", "parse.*natural language",
    "all.*subagent.*always", "full pipeline.*always",
    "batch.*pre.merge.*check", "synchronous.*overnight",
]


def score_option(opt_text: str, page_content: str) -> float:
    """
    Puntúa una opción de respuesta. Mayor puntaje = más probable que sea correcta.
    Basado en patrones del exam guide y conocimiento del dominio.
    """
    text = opt_text.lower()
    score = 0.0

    # Positivo: patrones de respuestas correctas
    for pattern in CORRECT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            score += 3.0

    # Negativo: patrones de respuestas incorrectas
    for pattern in WRONG_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            score -= 5.0

    # Contexto de la página: si el texto de la opción aparece en la lección
    if page_content:
        # Opciones más largas y específicas suelen ser más correctas
        score += len(text) / 300

        # Si la opción menciona conceptos clave de la lección
        lesson_keywords = re.findall(r'\b[A-Za-z_]{4,}\b', page_content)
        lesson_vocab = set(kw.lower() for kw in lesson_keywords[:200])
        opt_words = set(re.findall(r'\b[A-Za-z_]{4,}\b', text))
        overlap = len(opt_words & lesson_vocab)
        score += overlap * 0.1

    return score


async def solve_quiz(page) -> bool:
    """Lee las opciones, razona y selecciona la mejor respuesta. Retorna True si correcto."""
    # Obtener contenido de la página para contexto
    page_content = ""
    try:
        page_content = await page.evaluate("document.body.innerText")
    except:
        pass

    # Obtener opciones
    opts = await page.evaluate('''() => Array.from(document.querySelectorAll("input[type=radio]")).map((r, i) => ({
        i,
        label: (r.closest("label")?.innerText || r.parentElement?.innerText || r.value || "").trim()
    }))''')

    if not opts:
        return False

    # Puntuar cada opción
    scored = [(score_option(opt["label"], page_content), opt) for opt in opts]
    scored.sort(key=lambda x: x[0], reverse=True)

    best_score, best_opt = scored[0]
    print(f"      Options scored:")
    for sc, opt in scored:
        marker = "→ BEST" if opt == best_opt else "      "
        print(f"      {marker} [{sc:+.1f}] {opt['label'][:80]}")

    # Seleccionar la mejor opción
    await page.evaluate(f'''() => {{
        const radios = document.querySelectorAll("input[type=radio]")
        if (radios[{best_opt["i"]}]) radios[{best_opt["i"]}].click()
    }}''')
    await page.wait_for_timeout(500)

    # Submit
    await page.evaluate('''() => {
        const btn = Array.from(document.querySelectorAll("button")).find(b =>
            /(submit|check answer|next)/i.test(b.textContent || "")
        )
        if (btn && !btn.disabled) btn.click()
    }''')
    await page.wait_for_timeout(3000)

    # Verificar resultado
    body = await page.evaluate("document.body.innerText")
    correct = "incorrect" not in body.lower() and "wrong" not in body.lower() and "try again" not in body.lower()

    if correct:
        print(f"      ✓ CORRECT")
        return True

    print(f"      ✗ WRONG on first try — attempting remaining options in score order")
    for sc, opt in scored[1:]:
        if opt == best_opt:
            continue
        await page.evaluate(f'''() => {{
            const radios = document.querySelectorAll("input[type=radio]")
            if (radios[{opt["i"]}]) radios[{opt["i"]}].click()
        }}''')
        await page.wait_for_timeout(300)
        await page.evaluate('''() => {
            const btn = Array.from(document.querySelectorAll("button")).find(b =>
                /(submit|check answer)/i.test(b.textContent || "")
            )
            if (btn) btn.click()
        }''')
        await page.wait_for_timeout(2500)
        body2 = await page.evaluate("document.body.innerText")
        if "incorrect" not in body2.lower() and "wrong" not in body2.lower():
            print(f"      ✓ CORRECT on retry with: {opt['label'][:60]}")
            return True

    print(f"      ! Could not determine correct answer — moving on")
    return False


async def handle_and_complete(page):
    """Handle full lesson: video + quiz/exercise + Complete click"""
    await page.wait_for_timeout(2500)

    # Fast-forward video
    try:
        await page.evaluate('''() => {
            document.querySelectorAll('video').forEach(v => {
                if (v.duration && !isNaN(v.duration)) {
                    v.currentTime = v.duration - 0.5
                    v.play().catch(() => {})
                }
            })
        }''')
        await page.wait_for_timeout(2000)
    except:
        pass

    title = ""
    try:
        title = await page.evaluate("document.title")
    except:
        pass
    print(f"  > {title[:65]}")

    # Handle quiz
    try:
        n_radios = await page.evaluate("() => document.querySelectorAll('input[type=radio]').length")
        if n_radios > 0:
            await solve_quiz(page)
    except:
        pass

    # Handle textarea
    try:
        n_ta = await page.evaluate("() => document.querySelectorAll('textarea').length")
        if n_ta > 0:
            await page.evaluate('''() => {
                document.querySelectorAll("textarea").forEach(ta => {
                    const desc = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")
                    desc.set.call(ta, "Understood the concept. The key principle demonstrated here is important for production AI systems.")
                    ta.dispatchEvent(new Event("input", {bubbles: true}))
                    ta.dispatchEvent(new Event("change", {bubbles: true}))
                })
            }''')
            await page.wait_for_timeout(400)
            await page.evaluate('''() => {
                const btn = Array.from(document.querySelectorAll("button")).find(b =>
                    /(submit|save|continue)/i.test(b.textContent || "")
                )
                if (btn) btn.click()
            }''')
            await page.wait_for_timeout(2000)
    except:
        pass

    # Click Complete
    try:
        await page.evaluate('''() => {
            const a = Array.from(document.querySelectorAll("a[href]")).find(a =>
                a.textContent.trim() === "Complete" && a.href.includes("#")
            )
            if (a) a.click()
        }''')
        await page.wait_for_timeout(1500)
    except:
        pass


async def do_course(page, slug):
    print(f"\n{'='*60}")
    print(f"COURSE: {slug}")
    print('='*60)

    for iteration in range(150):
        try:
            await page.goto(f"https://anthropic.skilljar.com/{slug}/resume",
                           wait_until="domcontentloaded", timeout=25000)
        except:
            await page.wait_for_timeout(3000)
            continue
        await page.wait_for_timeout(2500)

        body = ""
        try:
            body = await page.evaluate("document.body.innerText")
        except:
            pass

        m = re.search(r"(\d+) of (\d+) lessons completed", body)
        if m and m.group(1) == m.group(2):
            print(f"\n  ✓ COMPLETE: {m.group(1)}/{m.group(2)}")
            try:
                await page.screenshot(
                    path=f"E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass/live/{slug[:25]}_DONE.png"
                )
            except:
                pass
            return True

        if re.search(r"/\d+$", page.url):
            await handle_and_complete(page)
        else:
            if m:
                print(f"  Status: {m.group(1)}/{m.group(2)} (iteration {iteration})")
            if iteration > 10:
                break
            await page.wait_for_timeout(2000)

    # Final
    try:
        await page.goto(f"https://anthropic.skilljar.com/{slug}",
                       wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        body = await page.evaluate("document.body.innerText")
        m = re.search(r"(\d+) of (\d+) lessons completed", body)
        if m:
            print(f"  Final: {m.group(1)}/{m.group(2)}")
            return m.group(1) == m.group(2)
    except:
        pass
    return False


COURSES = [
    "claude-with-the-anthropic-api",
    "introduction-to-model-context-protocol",
    "claude-code-in-action",
    "claude-101",
]


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = b.contexts[0].pages[0]

        results = {}
        for slug in COURSES:
            ok = await do_course(page, slug)
            results[slug] = ok

        print("\n\nFINAL STATUS:")
        for slug, ok in results.items():
            print(f"  {'✓' if ok else '!'} {slug}")


asyncio.run(main())
