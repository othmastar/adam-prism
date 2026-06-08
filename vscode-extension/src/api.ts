/**
 * Adam Prism API client
 */

export class AdamAPI {
  constructor(
    public endpoint: string,
    public apiKey: string = ''
  ) {}

  private get headers(): Record<string, string> {
    const h: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.apiKey) {
      h['Authorization'] = `Bearer ${this.apiKey}`;
    }
    return h;
  }

  async chat(message: string): Promise<string> {
    try {
      const response = await fetch(`${this.endpoint}/api/chat`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ message }),
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      return data.response || 'No response';
    } catch (err: any) {
      return `⚠️ Connection error: ${err.message}`;
    }
  }

  async *chatStream(message: string): AsyncGenerator<string> {
    try {
      const response = await fetch(`${this.endpoint}/api/engine/stream`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ message }),
      });
      if (!response.ok) throw new Error(`Stream error: ${response.status}`);
      const reader = response.body?.getReader();
      if (!reader) return;
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        for (const line of text.split('\n')) {
          if (line.startsWith('data: ')) {
            yield line.slice(6);
          }
        }
      }
    } catch (err: any) {
      yield `⚠️ ${err.message}`;
    }
  }

  async status(): Promise<any> {
    try {
      const response = await fetch(`${this.endpoint}/api/status`);
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }
}
