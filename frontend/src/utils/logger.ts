type LogLevel = 'info' | 'warn' | 'error';

interface LogOptions {
  notify?: boolean;
  metadata?: Record<string, unknown>;
}

class Logger {
  private logLevel: LogLevel = 'error';

  public setLogLevel(level: LogLevel): void {
    this.logLevel = level;
  }

  public info(message: string, options?: LogOptions): void {
    this.log('info', message, options);
  }

  public warn(message: string, options?: LogOptions): void {
    this.log('warn', message, options);
  }

  public error(message: string, error?: unknown, options?: LogOptions): void {
    const errorMessage = error instanceof Error ? error.message : String(error);
    const fullMessage = error ? `${message}: ${errorMessage}` : message;
    this.log('error', fullMessage, options);
    
    if (options?.notify !== false && typeof window !== 'undefined') {
      this.showErrorNotification(fullMessage);
    }
  }

  private showErrorNotification(message: string): void {
    try {
      const { toast } = require('react-hot-toast');
      toast.error(message);
    } catch (e) {
      if (process.env.NODE_ENV !== 'production') {
        console.error('Toast notification failed:', e);
      }
    }
  }

  private log(level: LogLevel, message: string, options?: LogOptions): void {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      ...options?.metadata,
    };
    
    if (process.env.NODE_ENV !== 'production') {
      const logMethod = level === 'error' ? console.error : 
                        level === 'warn' ? console.warn : 
                        console.info;
      logMethod(`[${timestamp}] [${level.toUpperCase()}] ${message}`);
      
      if (options?.metadata) {
        logMethod('Metadata:', options.metadata);
      }
    }
    
    if (process.env.NODE_ENV === 'production') {
      this.sendLogToServer(logEntry);
    }
  }

  private sendLogToServer(logEntry: unknown): void {
    try {
      if (typeof window !== 'undefined') {
        const logQueue = this.getLogQueue();
        logQueue.push(logEntry);
        this.setLogQueue(logQueue);
        
        if (logQueue.length >= 10) {
          this.flushLogs();
        }
      }
    } catch (err) {
      if (process.env.NODE_ENV !== 'production') {
        console.error('Error sending log to server:', err);
      }
    }
  }

  private getLogQueue(): unknown[] {
    try {
      const stored = localStorage.getItem('log_queue');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  private setLogQueue(queue: unknown[]): void {
    try {
      localStorage.setItem('log_queue', JSON.stringify(queue));
    } catch {
      localStorage.removeItem('log_queue');
    }
  }

  private flushLogs(): void {
    const logQueue = this.getLogQueue();
    if (logQueue.length === 0) return;
    
    this.setLogQueue([]);
    
    fetch('/api/logs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ logs: logQueue }),
    }).catch(() => {
      const currentQueue = this.getLogQueue();
      this.setLogQueue([...logQueue, ...currentQueue]);
    });
  }
}

export const logger = new Logger(); 