// Define All Servo stuff
#include <Servo.h>

int servoPin1R = 2;
int servoPin2R = 3;
int servoPin3R = 4;
int servoPin1L = 5;
int servoPin2L = 6;
int servoPin3L = 7;

Servo servo1R, servo2R, servo3R, servo1L, servo2L, servo3L;

// Set servo calibration points

int cal_1R = 41;
int cal_2R = 125;
int cal_3R = 21;
int cal_1L = 115;
int cal_2L = 53;
int cal_3L = 122;

// Misc variables
int tok;

// Setup loop
void setup() {
  // Start Serial
  Serial.begin(115200);

  servo1R.attach(servoPin1R);
  servo2R.attach(servoPin2R);
  servo3R.attach(servoPin3R);
  servo1L.attach(servoPin1L);
  servo2L.attach(servoPin2L);
  servo3L.attach(servoPin3L);

  int count = 0;
  while (count < 4)
  {
    servo1R.write(cal_1R);
    servo2R.write(cal_2R);
    servo3R.write(cal_3R);

    servo1L.write(cal_1L);
    servo2L.write(cal_2L);
    servo3L.write(cal_3L);
    count++;
    delay(300);
  }
}

void loop() {
  // ************ Upload What we need to matlab *****************

  // shake 1
  Matlab_Handshake();
  int num_pts = serial_reader_single();
  Serial.println(num_pts);
  int pitch[num_pts];
  int yaw[num_pts];
  int roll[num_pts];
  delay(1);

  // shake 1.5
  Matlab_Handshake();
  int pow_leng = serial_reader_single();
  Serial.println(pow_leng);
  delay(1);

  // shake 2
  Matlab_Handshake();
  double TS = serial_reader_single();
  Serial.println(TS);
  delay(1);

  // shake 3
  Matlab_Handshake();
  for (int i = 0; i <= num_pts - 1; i++)
  {
    pitch[i] = serial_reader_single();
    Serial.println(pitch[i]);
    delay(1);
  }
  // shake 4
  Matlab_Handshake();
  for (int i = 0; i <= num_pts - 1; i++)
  {
    yaw[i] = serial_reader_single();
    Serial.println(yaw[i]);
    delay(1);
  }

  // shake 5
  Matlab_Handshake();
  for (int i = 0; i <= num_pts - 1; i++)
  {
    roll[i] = serial_reader_single();
    Serial.println(roll[i]);
    delay(1);
  }
  // **************** Test Loop and Zero ***************
  unsigned long loop_start = micros();
  for (int i = 0; i <= num_pts - 1; i++)
  {
    servo1R.write(cal_1R + pitch[0]);
    servo2R.write(cal_2R + yaw[0]);
    servo3R.write(cal_3R - roll[0]);
    servo1L.write(cal_1L - pitch[0]);
    servo2L.write(cal_2L - yaw[0]);
    servo3L.write(cal_3L + roll[0]);
    delayMicroseconds(TS);
  }
  unsigned long current_time = micros();
  unsigned long time_delta = (current_time - loop_start);
  double period = (time_delta) / 1000000;

  // shake 6
  Matlab_Handshake();
  

  // ************** Execute Experiment *****************

  // shake 7
  Matlab_Handshake();
  int flap_num = 20;
  
  for (int j = 0; j <= flap_num; j++)
  {
    unsigned long loop_start = micros();
    int count = 1;

    for (int i = 0; i <= num_pts - 1; i++)
    {
      if (i <= pow_leng)
      {
        analogWrite(10, 255);
      }

      else
      {
        analogWrite(10, 0);
      }

      servo1R.write(cal_1R + pitch[i]);
      servo2R.write(cal_2R + yaw[i]);
      servo3R.write(cal_3R - roll[i]);
      servo1L.write(cal_1L - pitch[i]);
      servo2L.write(cal_2L - yaw[i]);
      servo3L.write(cal_3L + roll[i]);
      delayMicroseconds(TS);
    }

    unsigned long current_time = micros();
    unsigned long time_delta = (current_time - loop_start);
    double period = (time_delta) / 1000000;
  }

  // Rezero motors and hold waiting for instructions

  int flag = 1;

  while (flag == 1)
  {
    servo1R.write(cal_1R);
    servo2R.write(cal_2R);
    servo3R.write(cal_3R);

    servo1L.write(cal_1L);
    servo2L.write(cal_2L);
    servo3L.write(cal_3L);
    delay(100);

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
