# Extension Guide for Other Usecase

The current implimentation is targeting PX4 usecase of Aerialist. 

Surrealist and Aerialist has also been privately extended to generate and execute navigation tests for the **[ANYmal robot](https://www.anybotics.com/robotics/anymal/)**. 


Here is a short guideline for future extensions to other robotic usescase based on the ANYmal experience:  
- Extend Aerialist to support running test cases for your robotic usecase. Follow Aerialist guide for details. 
- Implement usecase specific **Solution** for the test generation search taking [Solution.py](./surrealist/search/solution.py) (or one of its child classes) as parent. 
- Develop usecase specific **Search** process taking [Serach](./surrealist/search/search.py) (on one of its child classed)  as parent.
- Search for `# extension_hint:` in the code base to find places needing some small updates. 
- Define usecase specific seed scenarios based on the samples in the [experiments folder](./experiments/). 
