#include "opencv2/highgui/highgui.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include <iostream>
#include <stdio.h>
#include <math.h>

#define TRUE 1
#define FALSE 0

using namespace std;
using namespace cv;

int GrayScale(int a, int b);
/**
 * @function main
 */
int main( int argc, char** argv )
{
  Mat src, input;

  /// Load image
  input = imread( argv[1], 1 );
  cvtColor(input,src,CV_BGR2HSV);

  if( !src.data ){ 
    return -1;
    }
    double counter = 0;
    double bgCounter = 0;
    long int hueTotal = 0;
    // long int satTotal = 0;
    // long int valueTotal = 0;
    // double totalCounter = 0;
//Cycle through each pixel and print out the [0] element of each pixel
  for(int i = 0; i < src.rows; i++)
  {
    for(int j = 0; j < src.cols; j++){
	     //satTotal += (double)src.at<Vec3b>(i, j)[1];
       //valueTotal += (double)src.at<Vec3b>(i, j)[2];
       //totalCounter++;
      // printf("Location: (%d, %d) Hue: %d, Saturation: %d, Value: %d\n", i, j, src.at<Vec3b>(i, j)[0], src.at<Vec3b>(i, j)[1], src.at<Vec3b>(i, j)[2]);
      if(GrayScale(src.at<Vec3b>(i, j)[1], src.at<Vec3b>(i, j)[2]) == TRUE){
      	bgCounter++;
        // printf("Gray Scale Detected!\n");
      } else {
      	if((double)src.at<Vec3b>(i, j)[0] > 170) {
          hueTotal += 0;
          counter++;
        } else {
          hueTotal += (double)src.at<Vec3b>(i, j)[0];
          counter++;
        }
        // printf("Something\n");
        //printf("Value: %d, I: %d, J: %d\n",src.at<Vec3b>(i, j)[0], i, j);
      }
    }
  }
  // printf("Value Total:%ld, Counter: %f\n", valueTotal, counter);
  double hueAverage = 0;
  if(counter == 0){
    counter = 1;
  }
  hueAverage = hueTotal/counter;
  hueAverage = hueAverage * 2;
  if(bgCounter == 0){
    bgCounter = 1;
  }
  //printf("Saturation Average: %f\n", (satTotal/totalCounter));
  //printf("Value Average: %f\n", (valueTotal/totalCounter));
  printf("Color to Background: %f\n", (counter/bgCounter));
  printf("Average Color: %f\n", hueAverage);
  return 0;
}

int GrayScale(int a, int b){
  float saturationThreshold = 90;
  float valueThreshold = 80;
  int isGrayScale = 0;

  if(a < saturationThreshold){      
    isGrayScale = TRUE;     
  } else if (b < valueThreshold){
    isGrayScale = TRUE;
  } else {
    isGrayScale = FALSE;
  }
  return isGrayScale;
}
