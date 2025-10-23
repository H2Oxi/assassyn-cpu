# referance for nomal signal relationships

## pipestream

a[i]@cycle(i)  -----> fifo -----> a[i]@cycle(i+1)

a -> push data -> pop data -> a
     credit+1.....credit-1


## bypass
              
a[i]@cycle(i)  -----> fifo -----> a[i]@cycle(i+1)
|                                     |
|   ----------downstream------------  |         
a[i]@cycle(i)------------------->a[i]@cycle(i)
a[i+1]@cycle(i+1)<-------------a[i+1]@cycle(i+1)


## pipe stall

module1 ( wait(valid) ) ---> fifo ---> module2

