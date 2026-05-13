const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const app = express();
const PORT = 3005;
const ROOT_DIR = path.join(__dirname, '..');

app.use(cors());
app.use(express.json());

// Obtener estado de tareas
app.get('/api/tasks', (req, res) => {
    const tasksPath = path.join(ROOT_DIR, 'AGENTS_TASKS.md');
    if (fs.existsSync(tasksPath)) {
        const content = fs.readFileSync(tasksPath, 'utf-8');
        res.json({ content });
    } else {
        res.status(404).send('Tasks file not found');
    }
});

// Obtener estado de Ollama y modelos
app.get('/api/status', (req, res) => {
    exec('ollama list', (error, stdout) => {
        if (error) {
            return res.json({ ollama: 'offline', models: [] });
        }
        const lines = stdout.trim().split('\n').slice(1);
        const models = lines.map(line => {
            const parts = line.split(/\s+/);
            return { name: parts[0], size: parts[2], modified: parts[3] };
        });
        res.json({ ollama: 'online', models });
    });
});

// Obtener resumen del RAG
app.get('/api/rag', (req, res) => {
    const indexPath = path.join(ROOT_DIR, 'src', 'rag', 'index.json');
    if (fs.existsSync(indexPath)) {
        const stats = fs.statSync(indexPath);
        const data = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));
        res.json({ 
            lastUpdate: stats.mtime,
            chunks: data.length,
            files: [...new Set(data.map(d => d.file))].length
        });
    } else {
        res.json({ chunks: 0, files: 0 });
    }
});

app.listen(PORT, () => {
    console.log(`Jarvis Console API running at http://localhost:${PORT}`);
});
