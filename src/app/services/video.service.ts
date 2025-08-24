import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class VideoService {
  private apiUrl = 'http://localhost:8000'; // FastAPI
  private ws: WebSocket | null = null;

  constructor(private http: HttpClient) {}

  // 📌 1. Subir video al backend
  uploadVideo(file: File): Observable<{ session_id: string }> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<{ session_id: string }>(`${this.apiUrl}/upload`, formData);
  }

  // 📌 2. Conectarse al WebSocket para recibir frames
  connect(
    sessionId: string,
    onFrame: (frameUrl: string) => void,
    onAlert: () => void
  ): void {
    this.ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'frame') {
          // ⚡ Recibimos un frame en base64 → convertir a URL para <img>
          onFrame(`data:image/jpeg;base64,${data.frame}`);
        } else if (data.type === 'alert') {
          onAlert();
        }
      } catch (err) {
        console.error('❌ Error procesando mensaje WS:', err);
      }
    };

    this.ws.onerror = (err) => {
      console.error('❌ Error en WebSocket:', err);
    };

    this.ws.onclose = () => {
      console.log('🔌 WS cerrado');
    };
  }

  // 📌 3. Cerrar conexión
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
