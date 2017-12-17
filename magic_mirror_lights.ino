#include <Adafruit_NeoPixel.h>
#ifdef __AVR__
  #include <avr/power.h>
#endif

#define PIN 6
#define NUM_LED 36

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LED, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  #if defined (__AVR_ATtiny85__)
    if (F_CPU == 16000000) clock_prescale_set(clock_div_1);
  #endif
  
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  
  Serial.begin(9600);
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'
}
void loop() {
  if(Serial.available()) {
    String data = Serial.readString();
    Serial.print(data);
    if (data == "black") {
      Serial.print(data);
      turnOff();
    } else if (data == "white") {
      Serial.print(data);
//      rainbow(100);
      solidColor();
    } else if (data == "rainbow") {
      Serial.print(data);
      rainbow();  
    }
  }
}

void turnOff() {
  uint16_t i;
  for (i=0; i<strip.numPixels(); i++) {
    strip.setPixelColor(i, 0);
  }
  strip.show();
}

void solidColor() {
  uint16_t i;
  for (i=0; i<strip.numPixels(); i++) {
    uint32_t warmWhite = strip.Color(255, 147, 41);
    strip.setPixelColor(i, warmWhite);
  }
  strip.show();
}

void rainbow() {
  uint16_t i, j;

  for(j=0; j<256; j++) {
    for(i=0; i<strip.numPixels(); i++) {
      strip.setPixelColor(i, Wheel((i+j) & 255));
    }
    strip.show();
  }
}

// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
}
