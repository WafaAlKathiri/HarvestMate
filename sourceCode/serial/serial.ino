#include <Braccio.h>
#include <Servo.h>
 
 
Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_rot;
Servo wrist_ver;
Servo gripper;
 
 
void setup() 
{
  Serial.begin(2000000); 
  Braccio.begin();
 
  Serial.println("In the setup") ; 
  //Go to the initial position
 
 
  Braccio.ServoMovement(20,           90,  150, 30, 0,  0,  10);
 
  Braccio.ServoMovement(20,           180,  30, 90, 0,  0,  10);
  delay(2000);
 
  while(!Serial) {}
 
}
 
void loop() {
 
  if (Serial.available() > 0){
 
      Serial.println("There is a message") ;
      String message = Serial.readStringUntil('\n');
 
      int num, direction, M1, M2, M3, M4,M2_2,M4_2;
      char comma;

 
      int parsed = sscanf(message.c_str(), "%d,%d,%d,%d,%d,%d\n", &num, &direction, &M1, &M2, &M3, &M4);
 
 
      Serial.println(num) ;
 
      if ( num == 1 )
          {
            Serial.println(M1) ;
            Serial.println(M2) ;
            Serial.println(M3) ;
            Serial.println(M4) ;
            Serial.println(direction) ;
            M4 = M4 + 15;
 
            Braccio.ServoMovement(20,           90,  150, 30, 0,  0,  10);
            delay(1000);
 
            Braccio.ServoMovement(20,           M1,  M2, M3, M4,  0,  10);
            delay(1000);
 
            Braccio.ServoMovement(20,           M1,  M2, M3, M4,  0,  70);
            delay(1000);
 
            if (direction == 1)
            {
              M2_2 = M2 + 15;
              if (M2_2 > 165)
              {
                M2_2 = 165;
              }
 
              M4_2 = 10 ;

 
              Braccio.ServoMovement(20,           M1,  M2_2, M3, M4_2,  0,  70);
              delay(2000);
            }
 
            if (direction == 0)
            {
              Braccio.ServoMovement(20,           M1,  M2, M3, 0,  0,  70);
              delay(2000);
            }
 
 
            Braccio.ServoMovement(20,           0,  90, 160, 180,  0,  70);
            delay(500);
 
            Braccio.ServoMovement(20,           90,  90, 180, 180,  0,  70);
            delay(500);
 
            // verification
            Braccio.ServoMovement(20,           115,  90, 160, 135,  0,  60);
            delay(500);
          }
 
      else if( num == 2 )
          {
 
            Braccio.ServoMovement(20,           60,  150, 170, 135,  0,  70);
            delay(500);
            Braccio.ServoMovement(20,           60,  150, 170, 135,  0,  10);
            delay(500);        
            Braccio.ServoMovement(20,           180,  30, 90, 0,  0,  10);
            delay(500);          
	          //sort the ripe fruit and go to the initial position
 
          }
 
      else if( num == 3 )
          {
            Braccio.ServoMovement(20,           120,  150, 170, 130,  0,  70);
            delay(500);
            Braccio.ServoMovement(20,           120,  150, 170, 130,  0,  10);
            delay(500);
            Braccio.ServoMovement(20,           180,  30, 90, 0,  0,  10);
            delay(500);
 
	          //sort the rotten fruit and go to the initial position
 
          }
 
      else if ( num == 4 ) 
          {
 
            Braccio.ServoMovement(20,           180,  30, 90, 0,  0,  10);
            delay(500);
 
            //Go to the initial position
          }
 
  }   
 
}
 