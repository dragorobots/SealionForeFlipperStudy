#include <Servo.h>

byte servoPin1 = 2;
byte servoPin2 = 3;
byte servoPin3 = 4;
byte servoPin4 = 5;
byte servoPin5 = 6;
byte servoPin6 = 7;

int tok;

Servo servo1, servo2, servo3, servo4, servo5, servo6;

// Set initial stuff
int percent_power;
int servo1_pwm;
int servo2_pwm;
int servo3_pwm; 
int servo4_pwm;
int servo5_pwm; 
int servo6_pwm;

void setup() {

  Serial.begin(115200);
  servo1.attach(servoPin1);
  servo2.attach(servoPin2);
  servo3.attach(servoPin3);
  servo4.attach(servoPin4);
  servo5.attach(servoPin5);
  servo6.attach(servoPin6);

  // set everything to all zeros
  servo1.writeMicroseconds(0); // send "stop" signal to ESC.
  servo2.writeMicroseconds(0); // send "stop" signal to ESC.
  servo3.writeMicroseconds(0); // send "stop" signal to ESC.
  servo4.writeMicroseconds(0); // send "stop" signal to ESC.
  servo5.writeMicroseconds(0); // send "stop" signal to ESC.
  servo6.writeMicroseconds(0); // send "stop" signal to ESC.
  delay(7000); // delay to allow the ESC to recognize the stopped signal

}

void loop() {

  // Shake 1
  Matlab_Handshake();
  delay(1000);
  percent_power = serial_reader_single();
  Serial.println(percent_power);
  delay(1000);

  // Shake 2
  Matlab_Handshake();
  delay(100);


// Spin up motors
    servo1_pwm = map(100, 0, 100, 500, 1600);
    servo2_pwm = map(100, 0, 100, 500, 1600);
    servo3_pwm = map(100, 0, 100, 500, 1600);
    servo4_pwm = map(100, 0, 100, 500, 1600);
    servo5_pwm = map(100, 0, 100, 500, 1600);
    servo6_pwm = map(100, 0, 100, 500, 1600);
    //

    servo1.writeMicroseconds(servo1_pwm);
    servo2.writeMicroseconds(servo2_pwm);
    servo3.writeMicroseconds(servo3_pwm);
    servo4.writeMicroseconds(servo4_pwm);
    servo5.writeMicroseconds(servo5_pwm);
    servo6.writeMicroseconds(servo6_pwm);
    delay(8000);
    
for (int i = 0; i <= percent_power; i += 5)
  {

    servo1_pwm = map(percent_power, 0, 100, 500, 1600);
    servo2_pwm = map(percent_power, 0, 100, 500, 1600);
    servo3_pwm = map(percent_power, 0, 100, 500, 1600);
    servo4_pwm = map(percent_power, 0, 100, 500, 1600);
    servo5_pwm = map(percent_power, 0, 100, 500, 1600);
    servo6_pwm = map(percent_power, 0, 100, 500, 1600);
    //

    servo1.writeMicroseconds(servo1_pwm);
    servo2.writeMicroseconds(servo2_pwm);
    servo3.writeMicroseconds(servo3_pwm);
    servo4.writeMicroseconds(servo4_pwm);
    servo5.writeMicroseconds(servo5_pwm);
    servo6.writeMicroseconds(servo6_pwm);
    delay(1000);
  }
}

/// ---------------------------Suppotting functions-----------------------------------
//------------------------------------------------------------------------------------

void clear_serial()
{
  Serial.flush();
  while (Serial.available() > 0)
  {
    Serial.read();
  }
}

double serial_reader_single()
{
  if (Serial.available() > 0) {
    tok = Serial.parseInt();
    return tok;
  }
  else
  {
    Serial.println("Nothing Recieved from Matlab");
  }
}

void Matlab_Handshake()
{
  int flag = 0;
  while (flag == 0)
  {
    while (Serial.available() > 0)
    {
      tok = Serial.parseInt();

      if (tok == 54321)
      { Serial.println(12345);
        clear_serial();
        delay(50);
        flag = 1;
        break;
      }
    }
  }
}
