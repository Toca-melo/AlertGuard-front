import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VideoService } from '../services/video.service';

@Component({
  selector: 'app-analisis-video',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analisis-video.component.html',
  styleUrls: ['./analisis-video.component.css']
})
export class AnalisisVideoComponent {
  statusMessage = '';
  frameUrl: string | null = null; // Aquí guardamos la URL del frame
  private sessionId: string | null = null;

  constructor(private videoService: VideoService) {}

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

    const file = input.files[0];
    this.statusMessage = 'Subiendo...';

    this.videoService.uploadVideo(file).subscribe({
      next: (res) => {
        this.sessionId = res.session_id;
        this.statusMessage = 'Procesando...';

        this.videoService.connect(
          this.sessionId,
          (url) => {
            // 👉 cada vez que llega un frame, lo pintamos
            this.frameUrl = url;
          },
          () => {
            this.statusMessage = '⚠️ ALERTA DETECTADA';
          }
        );
      },
      error: () => {
        this.statusMessage = 'Error al subir o procesar.';
      }
    });
  }

  ngOnDestroy() {
    this.videoService.disconnect();
  }
}
