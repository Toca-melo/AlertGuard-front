import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AnalisisVideoComponent } from './analisis-video/analisis-video.component';
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [AnalisisVideoComponent],
  template: `<app-analisis-video></app-analisis-video>`
})
export class AppComponent {
  title = 'frontAlertGuard';
}
