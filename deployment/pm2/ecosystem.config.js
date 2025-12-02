/**
 * PM2 Ecosystem Configuration
 * 
 * Configuration for running frontend and n8n workflows with PM2 (NO Docker).
 * 
 * This config uses environment variable PROJECT_ROOT or defaults to relative paths.
 * For production deployment, set PROJECT_ROOT environment variable.
 * 
 * Deployment:
 * 1. npm run build (in frontend directory)
 * 2. pm2 start ecosystem.config.js
 * 3. pm2 save
 * 4. pm2 startup
 * 
 * Usage:
 * - Development: cd deployment/pm2 && pm2 start ecosystem.config.js
 * - Production: PROJECT_ROOT=/opt/rideshare pm2 start ecosystem.config.js
 */

const path = require('path');
const projectRoot = process.env.PROJECT_ROOT || path.resolve(__dirname, '../..');

module.exports = {
  apps: [
    {
      name: 'rideshare-frontend',
      script: 'npm',
      args: 'start',
      cwd: path.join(projectRoot, 'frontend'),
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      error_file: path.join(projectRoot, 'logs', 'frontend-error.log'),
      out_file: path.join(projectRoot, 'logs', 'frontend-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    {
      name: 'n8n-workflows',
      script: 'n8n',
      cwd: projectRoot,
      env: {
        N8N_PORT: 5678,
        NODE_ENV: 'production'
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      error_file: path.join(projectRoot, 'logs', 'n8n-error.log'),
      out_file: path.join(projectRoot, 'logs', 'n8n-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};
