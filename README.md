# hours

## use SQLite to store events
update 2022-10-22

use _sqlgsheet.database_ to create and update the sqlite database

## update()

1. clean and transform the new events
2. update the db with _only_ new events
3. query the db for the events in the _reporting_year_ from the gsheet
4. create the reports _main_ and _subcategory_ and post to gsheet

## update steps

1. export the BlockyTime to email
2. download and save the .csv into the root directory as _events.csv_
3. run _update()_ from terminal

```
(env) >python blockytime.py
``` 