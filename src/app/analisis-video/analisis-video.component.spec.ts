import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnalisisVideoComponent } from './analisis-video.component';

describe('AnalisisVideoComponent', () => {
  let component: AnalisisVideoComponent;
  let fixture: ComponentFixture<AnalisisVideoComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AnalisisVideoComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(AnalisisVideoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
