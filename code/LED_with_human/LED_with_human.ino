#include <FastLED.h>

#define NUM_LEDS 1000
#define DATA_PIN 6
#define SENSOR_PIN 7 // 连接红外热释电传感器的pin口
int b;
int g;
int r;

CRGB leds[NUM_LEDS];
bool lastMotionState = false; // 记录上一次的运动状态

void setup() { 
    Serial.begin(9600);
    pinMode(SENSOR_PIN, INPUT);
    FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
}

void loop() {
    bool motion = digitalRead(SENSOR_PIN); // 读取传感器状态

    // 如果当前状态和上一次状态不同，那么打印状态并更新上一次状态
    if(motion != lastMotionState) {
        if(motion) {
            Serial.println("TrueMotion");
            fill_solid(leds, NUM_LEDS, CRGB(r, g, b));
            FastLED.show();
        } else {
            Serial.println("FalseMotion");
            fill_solid(leds, NUM_LEDS, CRGB(0, 0, 0)); // 可以设置LED为灭或者某种颜色
            FastLED.show();
        }
        lastMotionState = motion;
    }

    // 接受串口
    if(Serial.available()) {
      String rgbString = Serial.readStringUntil('\n');
      Serial.print("Received Signal: ");
      Serial.print(rgbString);
  
      int sep1 = rgbString.indexOf('_');
      int sep2 = rgbString.lastIndexOf('_');
      if(sep1 == -1 || sep2 == -1 || sep1 == sep2) {
          Serial.println("Data Format Error");
          return;
      }
      b = rgbString.substring(0, sep1).toInt();
      g = rgbString.substring(sep1 + 1, sep2).toInt();
      r = rgbString.substring(sep2 + 1).toInt();

      
      fill_solid(leds, NUM_LEDS, CRGB(r, g, b));
      if(motion){
        FastLED.show();
      }
      Serial.print("Change BGR: ");
        Serial.print(b);
        Serial.print("_");
        Serial.print(g);
        Serial.print("_");
        Serial.print(r);
        Serial.println();
    }

}
