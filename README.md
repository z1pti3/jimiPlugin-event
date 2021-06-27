# jimiPlugin-event
jimi SIEM functionality 


## Dev Notes

eventValues can contain additional data which is then presented within the UI. This is done by creating a new dict key with _data appended to the end. The start of the key MUST match the key of the list data. An example for how this works is shown:

```
{
"assets" ["abcd","efgh","ijkl"],
"assets_data": { "abcd" : { "name" : "test2", "ip" : "192.168.0.1" }, "efgh" : {}, "ijkl" : {} 
}
```

Doing this enables assets to be matched to additonal data within assets_data that can then be used to enrich data witin the UI
