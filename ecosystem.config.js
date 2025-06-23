module.exports = {
    apps: [{
      name: 'tphpy-api',
      script: 'api.py',
      interpreter: './venv/bin/python',
      cwd: '/var/www/html/TPHPY',
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/err.log',
      out_file: './logs/out.log',
      log_file: './logs/combined.log',
      time: true
    }]
  };