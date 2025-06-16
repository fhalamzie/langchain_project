module.exports = {
  apps: [{
    name: 'wincasa',
    script: '/home/projects/wincasa_llm/venv/bin/python',
    args: '-m streamlit run src/wincasa/core/benchmark_streamlit.py --server.port 8667 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false --server.headless true',
    cwd: '/home/projects/wincasa_llm',
    env: {
      PYTHONPATH: '/home/projects/wincasa_llm/src:/home/projects/wincasa_llm',
      PYTHONUNBUFFERED: '1',  // Critical for Python logging to show in PM2
      PATH: '/home/projects/wincasa_llm/venv/bin:' + process.env.PATH
    },
    interpreter: 'none',  // Don't use node interpreter
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: 'logs/pm2/wincasa-error.log',
    out_file: 'logs/pm2/wincasa-out.log',
    log_file: 'logs/pm2/wincasa-combined.log',
    time: true,  // Add timestamps to logs
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
    
    // Restart policy
    min_uptime: '10s',
    max_restarts: 10,
    restart_delay: 4000,
    
    // Shutdown settings
    kill_timeout: 30000,
    wait_ready: true,
    listen_timeout: 10000
  }]
}