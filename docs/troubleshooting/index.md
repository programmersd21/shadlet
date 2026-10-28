# troubleshooting

### common issues and solutions:

- **renderer dist not found**: 
  - If running from source, run `npm run build` in `packages/renderer`.
  - If installed via PyPI (`pip install shadlet`), static assets are pre-bundled and served automatically.

- **port in use**:
  - shadlet includes automatic port scanning and port switching. If the default port (8000) is occupied, the server automatically detects an open port and informs you in the terminal.

- **server disconnect / connection banner**:
  - If the backend server stops or reboots, a full-width top banner appears indicating `Server disconnected` with a live reconnect button and automatic exponential backoff retry.

- **hot reload issues**:
  - shadlet uses granular diff-based hot reload. When you save your Python files in `shadlet dev`, file changes are debounced (300ms window) and diff patches are sent over WebSocket, refreshing the component tree without triggering a full page reload or losing client state.

- **desktop build prerequisites**:
  - Run `shadlet doctor` to verify Node.js, npm, Electron, and PyInstaller availability.
  - Running `shadlet build` will automatically attempt to install missing desktop tools.
