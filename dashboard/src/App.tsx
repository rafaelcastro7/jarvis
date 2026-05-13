import React, { useEffect, useState } from 'react';
import { Activity, Database, ClipboardList, Cpu, RefreshCw, Zap } from 'lucide-react';
import { motion } from 'framer-motion';

interface SystemStatus {
  ollama: string;
  models: Array<{ name: string; size: string; modified: string }>;
}

interface RagStatus {
  lastUpdate: string;
  chunks: number;
  files: number;
}

interface Task {
  id: string;
  task: string;
  agent: string;
  status: string;
  priority: string;
}

const App: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [rag, setRag] = useState<RagStatus | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [statusRes, ragRes, tasksRes] = await Promise.all([
        fetch('http://localhost:3005/api/status'),
        fetch('http://localhost:3005/api/rag'),
        fetch('http://localhost:3005/api/tasks')
      ]);

      const statusData = await statusRes.json();
      const ragData = await ragRes.json();
      const tasksData = await tasksRes.json();

      setStatus(statusData);
      setRag(ragData);
      
      // Parse tasks from Markdown
      const taskLines = tasksData.content.split('\n');
      const parsedTasks: Task[] = [];
      taskLines.forEach((line: string) => {
        if (line.startsWith('| T-')) {
          const parts = line.split('|').map(s => s.trim());
          parsedTasks.push({
            id: parts[1],
            task: parts[2],
            agent: parts[3],
            status: parts[4],
            priority: parts[5]
          });
        }
      });
      setTasks(parsedTasks);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="dashboard">Cargando consola...</div>;

  return (
    <div className="dashboard">
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="header"
      >
        <h1>JARVIS <span style={{ fontWeight: 200, opacity: 0.5 }}>CONSOLE</span></h1>
        <div className="status-badge">
          <div className={`status-dot ${status?.ollama === 'online' ? '' : 'offline'}`} />
          Ollama System: {status?.ollama?.toUpperCase()}
        </div>
      </motion.header>

      <div className="grid">
        {/* RAG Card */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="card"
        >
          <h2><Database size={20} /> RAG Intelligence</h2>
          <div className="stats-value">{rag?.chunks || 0}</div>
          <div className="stats-label">Vector Chunks Indexados</div>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
            <div>
              <div style={{ fontWeight: 'bold' }}>{rag?.files || 0}</div>
              <div className="stats-label">Fuentes</div>
            </div>
            <div>
              <div style={{ fontWeight: 'bold' }}>Active</div>
              <div className="stats-label">Status</div>
            </div>
          </div>
        </motion.div>

        {/* System Load */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <h2><Cpu size={20} /> Local Models</h2>
          <div className="task-list">
            {status?.models.map(m => (
              <div key={m.name} className="model-tag">
                <Zap size={10} style={{ marginRight: 4 }} />
                {m.name} ({m.size})
              </div>
            ))}
          </div>
        </motion.div>

        {/* Tasks Card */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          style={{ gridColumn: 'span 2' }}
          className="card"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h2><ClipboardList size={20} /> Agent Task Board</h2>
            <RefreshCw size={16} className="spin" onClick={fetchData} style={{ cursor: 'pointer' }} />
          </div>
          <div className="task-list">
            {tasks.map(t => (
              <div key={t.id} className="task-item">
                <div>
                  <span className="task-id">{t.id}</span>
                  <span style={{ marginLeft: '1rem' }}>{t.task}</span>
                </div>
                <div style={{ display: 'flex', gap: '1.5rem' }}>
                  <span style={{ color: '#94a3b8' }}>{t.agent}</span>
                  <span style={{ 
                    color: t.status.includes('✅') ? '#22c55e' : '#f59e0b',
                    fontWeight: 'bold'
                  }}>{t.status}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      <motion.footer 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        style={{ marginTop: '4rem', textAlign: 'center', opacity: 0.5, fontSize: '0.875rem' }}
      >
        JARVIS LOCAL AI AGENT SYSTEM &copy; 2026 | Powered by Ollama & Antigravity
      </motion.footer>
    </div>
  );
};

export default App;
