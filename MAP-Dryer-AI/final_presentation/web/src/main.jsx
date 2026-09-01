import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './styles.css';

// StrictMode is deliberately off: React Three Fiber double-invokes effects
// under it, which would build the world twice and start two GSAP timelines.
createRoot(document.getElementById('root')).render(<App />);
