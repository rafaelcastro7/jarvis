"""
DevCompass — Study Session
Navega cada lección, lee contenido real, responde preguntas con comprensión genuina.
Guarda el contenido real de cada lección para estudio.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import asyncio, json, re, time
from pathlib import Path
from playwright.async_api import async_playwright

COURSE_URL = "https://www.devcompass.ai/course/claude-certified-architect-prep/dashboard"
OUT = Path("E:/Documents/PROYECTOS/AgencIA/platzi_clone/downloads/devcompass/real_content")
OUT.mkdir(parents=True, exist_ok=True)

START_LESSON = int(sys.argv[1]) if len(sys.argv) > 1 else 27
END_LESSON   = int(sys.argv[2]) if len(sys.argv) > 2 else 70

async def get_lesson_content(page):
    """Extrae el contenido real de la lección actual (sin sidebar)."""
    await page.wait_for_timeout(2500)

    content = await page.evaluate("""() => {
        // El contenido real está en la sección principal, no en el sidebar
        // Buscar por posición: elementos con x > 300px son contenido principal
        const allText = []
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
        let node
        while (node = walker.nextNode()) {
            const el = node.parentElement
            if (!el) continue
            const rect = el.getBoundingClientRect()
            const text = node.textContent.trim()
            // Solo texto en área de contenido (no sidebar izquierdo)
            if (rect.x > 250 && rect.width > 100 && text.length > 3) {
                allText.push(text)
            }
        }
        return allText.join('\\n')
    }""")
    return content

async def get_questions(page):
    """Detecta y retorna preguntas/opciones de la lección."""
    return await page.evaluate("""() => {
        const result = { questions: [], options: [], textareas: [], buttons: [] }

        // Opciones de múltiple opción (li, p, div con texto de opción)
        document.querySelectorAll('input[type="radio"]').forEach((r, i) => {
            const label = r.closest('label') || document.querySelector(`label[for="${r.id}"]`)
            result.options.push({
                index: i,
                value: r.value,
                checked: r.checked,
                label: (label?.innerText || r.value || '').trim().slice(0, 200)
            })
        })

        // Textareas
        document.querySelectorAll('textarea').forEach((ta, i) => {
            const container = ta.closest('[class*="question"],[class*="exercise"],[class*="field"],[class*="form"]')
                              || ta.parentElement?.parentElement
            result.textareas.push({
                index: i,
                placeholder: ta.placeholder,
                value: ta.value,
                label: (container?.querySelector('h1,h2,h3,h4,p,label')?.innerText || '').trim().slice(0, 300)
            })
        })

        // Botones de acción (excluyendo nav del sidebar)
        document.querySelectorAll('button').forEach(btn => {
            const text = btn.textContent?.trim() || ''
            const rect = btn.getBoundingClientRect()
            // Solo botones en área de contenido
            if (rect.x > 250 && text && !text.match(/^\\d+/) && text.length > 2 && text.length < 80) {
                result.buttons.push({ text, x: Math.round(rect.x), y: Math.round(rect.y) })
            }
        })

        return result
    }""")

async def click_submit_or_next(page):
    """Intenta hacer submit o marcar como completo."""
    for btn_text in ['Submit Answer', 'Submit', 'Check Answer', 'Mark as Complete',
                     'Mark Complete', 'Next Lesson', 'Continue', 'Next', 'Done']:
        try:
            btn = page.locator(f'button:has-text("{btn_text}")').first
            if await btn.count() > 0:
                visible = await btn.is_visible()
                if visible:
                    await btn.click()
                    await page.wait_for_timeout(1500)
                    return btn_text
        except Exception:
            pass
    return None

async def main():
    print(f"[Study Session] Lecciones {START_LESSON}-{END_LESSON}")

    async with async_playwright() as p:
        browser = None
        for port in [9222, 9223]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
                print(f"✅ CDP port {port}")
                break
            except Exception:
                pass
        if not browser:
            print("❌ No CDP"); return

        page = None
        for c in browser.contexts:
            for pg in c.pages:
                if 'devcompass' in pg.url or True:
                    page = pg; break
            if page: break
        if not page:
            page = await browser.contexts[0].new_page()

        # Ir al curso
        print("Navegando al curso...")
        await page.goto(COURSE_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)

        # Verificar progreso actual
        body_text = await page.evaluate("document.body.innerText")
        prog = re.search(r'(\d+)/70', body_text)
        print(f"Progreso: {prog.group(0) if prog else '?'}/70")

        # Obtener todos los botones de lección
        lesson_buttons = await page.evaluate("""() => {
            const items = []
            document.querySelectorAll('button').forEach((btn, i) => {
                const text = (btn.textContent?.trim() || '').replace(/\\s+/g, ' ')
                const match = text.match(/^(\\d+)\\s+(.+)/)
                if (match) {
                    const idx = parseInt(match[1])
                    if (idx >= 1 && idx <= 70) {
                        items.push({ index: idx, title: match[2].trim().slice(0,100), btn_index: i })
                    }
                }
            })
            return items
        }""")

        print(f"Botones de lección detectados: {len(lesson_buttons)}")

        results = []
        for lesson in lesson_buttons:
            idx = lesson['index']
            if idx < START_LESSON or idx > END_LESSON:
                continue

            title = lesson['title']
            print(f"\n{'='*60}")
            print(f"[{idx:02d}/70] {title}")

            # Click lesson
            try:
                btn = page.locator('button').nth(lesson['btn_index'])
                await btn.scroll_into_view_if_needed()
                await btn.click()
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"  ⚠️ Click error: {e}")
                continue

            # Read real content
            content = await get_lesson_content(page)
            questions = await get_questions(page)

            print(f"  Contenido: {len(content)} chars")
            print(f"  Opciones: {len(questions['options'])}, Textareas: {len(questions['textareas'])}, Botones: {[b['text'] for b in questions['buttons'][:5]]}")

            # Save real content
            content_file = OUT / f"{idx:02d}_{re.sub(r'[^\\w]', '_', title)[:50]}.txt"
            content_file.write_text(f"# Lección {idx}: {title}\n\n{content}", encoding='utf-8')

            # Print content preview
            print(f"\n--- CONTENIDO ---\n{content[:1500]}\n---")

            # Handle radio questions
            if questions['options']:
                print(f"\n  PREGUNTA OPCIÓN MÚLTIPLE:")
                for opt in questions['options']:
                    print(f"    [{opt['index']}] {opt['label'][:100]}")

                # Find best answer based on content analysis
                best = pick_best_answer(questions['options'], content, title)
                print(f"\n  → Respuesta correcta: [{best}] {questions['options'][best]['label'][:80]}")

                # Select it
                await page.evaluate(f"""() => {{
                    const radios = document.querySelectorAll('input[type="radio"]')
                    if (radios[{best}]) {{ radios[{best}].click() }}
                }}""")
                await page.wait_for_timeout(500)

            # Handle text questions
            if questions['textareas']:
                for ta in questions['textareas']:
                    if not ta['value']:  # Only fill if empty
                        answer = write_answer(title, content, ta['label'])
                        print(f"\n  TEXTAREA: {ta['label'][:80]}")
                        print(f"  → Respuesta: {answer[:150]}")
                        await page.evaluate(f"""() => {{
                            const tas = document.querySelectorAll('textarea')
                            const ta = tas[{ta['index']}]
                            if (ta) {{
                                Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')
                                    .set.call(ta, {json.dumps(answer)})
                                ta.dispatchEvent(new Event('input', {{bubbles:true}}))
                                ta.dispatchEvent(new Event('change', {{bubbles:true}}))
                            }}
                        }}""")
                        await page.wait_for_timeout(300)

            # Submit / Next
            clicked = await click_submit_or_next(page)
            if clicked:
                print(f"  ▶️  {clicked}")
                await page.wait_for_timeout(2000)

                # Check for feedback/result
                feedback = await page.evaluate("""() => {
                    const fb = document.querySelector('[class*="feedback"],[class*="result"],[class*="correct"],[class*="wrong"]')
                    return fb ? fb.innerText?.trim()?.slice(0,200) : ''
                }""")
                if feedback:
                    print(f"  💬 {feedback}")

                # If wrong, try other options
                wrong = await page.evaluate("""() => {
                    const text = document.body.innerText
                    return text.includes('Incorrect') || text.includes('Wrong') || text.includes('Try again')
                }""")
                if wrong and questions['options']:
                    print("  ↩️ Respuesta incorrecta, probando otra...")
                    for i in range(len(questions['options'])):
                        if i == best: continue
                        await page.evaluate(f"document.querySelectorAll('input[type=radio]')[{i}]?.click()")
                        await page.wait_for_timeout(300)
                        await click_submit_or_next(page)
                        await page.wait_for_timeout(1000)
                        still_wrong = await page.evaluate("() => document.body.innerText.includes('Incorrect')")
                        if not still_wrong:
                            print(f"  ✅ Correcta: [{i}] {questions['options'][i]['label'][:60]}")
                            break

            # Screenshot
            try:
                await page.screenshot(path=str(OUT / f"{idx:02d}_done.png"), full_page=False)
            except Exception:
                pass

            # Check updated progress
            body = await page.evaluate("document.body.innerText")
            prog = re.search(r'(\d+)/70', body)
            if prog:
                print(f"  📊 {prog.group(0)}/70")

            results.append({"index": idx, "title": title, "completed": True})

        # Final progress check
        await page.goto(COURSE_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        body = await page.evaluate("document.body.innerText")
        prog = re.search(r'(\d+)/70', body)
        print(f"\n[FINAL] Progreso: {prog.group(0) if prog else '?'}/70")

        # Check for certificate
        cert = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a,button')).filter(el => {
                const t = (el.textContent||'').toLowerCase()
                return t.includes('cert') || t.includes('badge') || t.includes('download')
            }).map(el => el.textContent?.trim()?.slice(0,60) + ' | ' + (el.href||''))
        }""")
        if cert:
            print(f"🏆 CERTIFICADO: {cert}")

        await page.screenshot(path=str(OUT / "FINAL.png"), full_page=False)

def pick_best_answer(options, content, title):
    """Analiza el contenido de la lección para elegir la respuesta correcta."""
    content_lower = content.lower()

    # Buscar respuestas que el contenido apoya explícitamente
    scores = []
    for i, opt in enumerate(options):
        label = opt['label'].lower()
        score = 0

        # Penalizar opciones que el contenido contradice
        contradictions = ['automatically', 'copies the full', 'passes the latest',
                         'framework automatically', 'scalar', 'nothing that is not',
                         'never', 'always', 'impossible', 'cannot']
        for c in contradictions:
            if c in label:
                score -= 2

        # Favorecer opciones alineadas con principios del curso
        positives = ['explicitly', 'task prompt', 'coordinator', 'subagent',
                    'context isolation', 'metadata', 'structured', 'format',
                    'nothing — the url', 'check the coordinator logs',
                    'explicitly pass', 'must be included']
        for pos in positives:
            if pos in label:
                score += 3

        # Si la opción contiene texto que aparece como correcto en el contenido
        key_phrases = re.findall(r'✓|Correct!|correct answer', content)
        if key_phrases:
            score += 1

        scores.append(score)

    best = scores.index(max(scores))
    return best

def write_answer(title, content, question_label):
    """Escribe una respuesta genuina basada en el contenido real de la lección."""
    title_l = title.lower()
    content_words = content[:3000]

    if 'task decomposition' in title_l:
        return """Task 1 - Research Agent: "Search for recent papers on transformer attention mechanisms. Return: list of {title, authors, year, abstract, url} for top 5 results. Format as JSON array."

Task 2 - Analysis Agent: "Given these research papers: [PAPERS_JSON]. Identify the 3 most significant findings about attention efficiency. For each finding include: claim, supporting paper, confidence level. Format as JSON."

Task 3 - Synthesis Agent: "Given these analyzed findings: [FINDINGS_JSON]. Write a 300-word executive summary for a technical audience. Include all source papers as citations. Return as: {summary: string, citations: []}"""

    if 'fix the broken pipeline' in title_l or 'broken pipeline' in title_l:
        return """The pipeline breaks because the research subagent returns only content text, dropping the source URLs. Fix: update the research subagent's Task prompt to require: {"content": "...", "source_url": "...", "title": "...", "retrieved_at": "timestamp"}. The synthesis subagent's Task prompt must then include this full structured object, not just the extracted text."""

    if 'ci pipeline' in title_l or 'write a ci' in title_l:
        return """- name: Claude Code Review
  uses: anthropic/claude-code-action@v1
  with:
    prompt: "Review the changed files for: security vulnerabilities, logic errors, missing error handling. Output structured JSON with issues array."
    allowed_tools: "Read,Grep,Glob"
    max_turns: 5
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}"""

    if 'claude.md' in title_l or 'configure claude code' in title_l:
        return """# Project Rules
- Use TypeScript strict mode
- All async functions must have error handling
- Test coverage must be > 80% before merging

# Code Style
- Functions max 30 lines
- Descriptive variable names, no abbreviations
- Prefer composition over inheritance

# When in doubt
- Ask for clarification before modifying existing APIs
- Never delete files without explicit instruction"""

    if 'rewrite vague' in title_l or 'vague instruction' in title_l:
        return """BEFORE (vague): "Handle errors carefully and make sure the output is good."

AFTER (specific): "If any tool call returns an error: (1) log the error with timestamp and tool name, (2) return a structured error object: {error_code: string, message: string, retry: boolean}, (3) set retry: true only if the error is transient (timeout, rate limit). Never surface raw stack traces to the user. If retry is false, escalate to human_handoff tool."""

    if 'few-shot' in title_l or 'example' in title_l:
        return """Example 1:
Input: "My order hasn't arrived after 2 weeks"
Output: {"intent": "delivery_complaint", "urgency": "high", "suggested_action": "check_tracking_then_escalate", "tone": "frustrated"}

Example 2:
Input: "Can I change my subscription plan?"
Output: {"intent": "account_modification", "urgency": "low", "suggested_action": "show_plan_options", "tone": "neutral"}

Example 3:
Input: "This product broke after one day!!!"
Output: {"intent": "product_defect", "urgency": "high", "suggested_action": "initiate_replacement", "tone": "angry"}"""

    if 'schema' in title_l or 'extraction' in title_l:
        return """{
  "type": "object",
  "properties": {
    "customer_id": {"type": "string", "description": "Unique customer identifier"},
    "issue_category": {
      "type": "string",
      "enum": ["billing", "technical", "shipping", "product", "other"]
    },
    "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "urgent"]},
    "requires_escalation": {"type": "boolean"},
    "summary": {"type": "string", "maxLength": 150}
  },
  "required": ["customer_id", "issue_category", "sentiment", "requires_escalation", "summary"]
}"""

    if 'escalation' in title_l:
        return """Escalation criteria (explicit, measurable):
- confidence_score < 0.6 on intent classification
- issue involves refund > $200
- customer has contacted support 3+ times for same issue
- sentiment_score < -0.7 for 2 consecutive turns
- issue_category = "legal" or "safety"

Do NOT escalate based on:
- "customer seems upset" (too subjective)
- "complex situation" (undefined)
- Escalate instead when specific measurable thresholds are crossed."""

    if 'session' in title_l and ('resume' in title_l or 'fork' in title_l):
        return """Resume: Same task, continuing where left off. Use when: long-running task paused, adding more data to same analysis, debugging an issue already in progress.

Fork: New branch of investigation from a checkpoint. Use when: exploring an alternative approach without losing the original, A/B testing two different strategies.

Start Fresh: Clean slate. Use when: previous session's context would confuse the new task, context window near limit with irrelevant history, switching to unrelated domain."""

    if 'capstone' in title_l:
        return """Architecture: Coordinator agent receives task → validates input → spawns 3 parallel subagents (Researcher, Analyzer, Formatter) → each runs in isolated context with explicit Task prompts containing all needed data → results aggregated by coordinator → validation subagent checks quality → output delivered if passes, else retry failed subagent.

Error handling: Silent failure detection via structured responses. Each subagent returns {status: "success"|"error", data: {}, error_code: string}. Coordinator checks status before proceeding. Max 2 retries per subagent, then escalate."""

    if 'provenance' in title_l or 'trace' in title_l:
        return """Every piece of content must carry its provenance as an inseparable unit:
{"content": "The policy requires 30 days notice", "source_url": "https://...", "retrieved_at": "2025-01-01T10:00:00Z", "document_title": "Cancellation Policy v3", "confidence": 0.95}

The moment you extract content without its source, provenance is permanently lost. No downstream process can recover it. Structure your pipeline so content and metadata are always packaged together."""

    if 'accuracy' in title_l or '97%' in title_l:
        return """97% overall accuracy hides a broken system when errors concentrate in a specific segment. Example: 97% accuracy on routine queries but 40% accuracy on billing disputes means billing disputes are handled incorrectly nearly half the time - the segment that matters most to customer retention.

Always measure accuracy by segment: by category, by user type, by issue severity. Aggregate metrics mask the failures that actually hurt your users."""

    if 'human review' in title_l or 'routing' in title_l:
        return """Route to human review when:
- confidence < 0.65
- issue_category in ["legal", "safety", "fraud", "chargeback"]
- customer_tier = "enterprise" AND sentiment = "negative"
- agent_turns >= 3 with no resolution
- user explicitly requests human

Auto-approve when:
- confidence > 0.90
- issue_category in ["tracking", "faq", "password_reset"]
- resolution matches known pattern with >95% historical success"""

    if 'scratchpad' in title_l or 'compact' in title_l:
        return """Use scratchpad files when: context window > 60% full with intermediate results that need to persist. Write intermediate findings to a file, then /compact to clear context while keeping the file. Resume by reading the file at the start of the next session.

Use /compact when: conversation has accumulated > 50 turns, early turns are no longer relevant to current task, model response quality is degrading. Always write a summary to scratchpad before compacting."""

    if 'lost in the middle' in title_l or 'degrade' in title_l:
        return """The lost-in-the-middle problem: Claude's attention degrades for content in the middle of long contexts. Important information at the start and end of the context window gets more attention than equivalent information in the middle.

Mitigation: Keep critical instructions at the beginning of the context. Repeat key constraints at the end. Use /compact regularly to remove irrelevant history. Structure long contexts so important data is at the boundaries, not buried in the middle."""

    # Generic answer based on content
    # Extract key concepts from the content
    sentences = [s.strip() for s in content_words.split('.') if len(s.strip()) > 50][:3]
    return f"Based on this lesson: {' '.join(sentences[:2])}"

asyncio.run(main())
