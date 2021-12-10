# emP:ty admin program

emP:ty의 main server로부터 초기 주차공간 좌표를 전달받고 해당 좌표를 수정, 추가 및 indexing하는 프로그램.

### run
1. set config.py
 ```
 SERVER_URL = server url
 TEST_IMAGE = image path for testing
 TEST_YML = yml path for testing
 ```
2. run
 ```
 python main.py
 ```
 
 * for Test, use this
 ```
 python main.py -t
 ```
3. Manual
![image](https://user-images.githubusercontent.com/42057488/145519165-fb19aa76-1c76-47de-8997-6feccbba8347.png)
- To draw new lot, Left Click the corner points of it.
- When you want to stop drawing new lot, Press 'R' to Reset.
- To delete a lot, Right Click the polygon.
- To sort the indices and make the table of parking lots, Press 'S' to Sort
