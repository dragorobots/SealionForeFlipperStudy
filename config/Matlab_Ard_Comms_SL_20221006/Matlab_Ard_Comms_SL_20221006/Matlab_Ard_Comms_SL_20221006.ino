// Define All Servo stuff
#include <Servo.h>

int servoPin1 = 2;
int servoPin2 = 3;
int servoPin3 = 4;

int signal_pin=10;

Servo servo1, servo2, servo3;

// Set servo calibration points

int cal_1 = 40;
int cal_2 = 135;
int cal_3 = 50;

// Misc variables
int tok;

// Setup loop
void setup() {
  // Start Serial
  Serial.begin(115200);

  servo1.attach(servoPin1);
  servo2.attach(servoPin2);
  servo3.attach(servoPin3);

  int count = 0;
  while (count < 4)
  {
    servo1.write(cal_1);
    servo2.write(cal_2);
    servo3.write(cal_3);

    count++;
    delay(300);
  }
}

void loop() {
  // ************ Upload What we need to matlab *****************

  // shake 1
  // Get trajectory length and intialize the arrays
  Matlab_Handshake();
  int num_pts = serial_reader_single();
  Serial.println(num_pts);
  int pitch[num_pts];
  int yaw[num_pts];
  int roll[num_pts];
  delay(1);

  // shake 1.5
  // get individual trial duration
  Matlab_Handshake();
  int pow_leng = serial_reader_single();
  Serial.println(pow_leng);
  delay(1);

  // shake 2
  // time step
  Matlab_Handshake();
  double TS = serial_reader_single();
  Serial.println(TS);
  delay(1);

  // shake 3
  // get pitch trajectory
  Matlab_Handshake();
  for (int i = 0; i <= num_pts - 1; i++)
  {
    pitch[i] = serial_reader_single();
    Serial.println(pitch[i]);
    delay(1);
  }
  
  // shake 4
  // get yaw trajectory
  Matlab_Handshake();
  for (int i = 0; i <= num_pts - 1; i++)
  {
    yaw[i] = serial_reader_single();
    Serial.println(yaw[i]);
    delay(1);
  }

  // shake 5 
  // get roll trajectory
  Matlab_Handshake();
  for (int i = 0; i <= num_pts - 1; i++)
  {
    roll[i] = serial_reader_single();
    Serial.println(roll[i]);
    delay(1);
  }
  // **************** Test Loop and Zero ***************
  
  // shake 6
  Matlab_Handshake();
  unsigned long loop_start = micros();
  for (int i = 0; i <= num_pts - 1; i++)
  {
    servo1.write(cal_1 + pitch[0]);
    servo2.write(cal_2 + yaw[0]);
    servo3.write(cal_3 + roll[0]);

    delayMicroseconds(TS);
  }
  unsigned long current_time = micros();
  unsigned long time_delta = (current_time - loop_start);
  double period = (time_delta) / 1000000;

  

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
      // Send signal during only power stroke duration
      if (i <= pow_leng)
      {
        analogWrite(signal_pin, 255);
      }

      else
      {
        analogWrite(signal_pin, 0);
      }

      // Move motors
      servo1.write(cal_1 + pitch[i]);
      servo2.write(cal_2 + yaw[i]);
      servo3.write(cal_3 + roll[i]);

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
    servo1.write(cal_1);
    servo2.write(cal_2);
    servo3.write(cal_3);
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
