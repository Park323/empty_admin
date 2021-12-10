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
