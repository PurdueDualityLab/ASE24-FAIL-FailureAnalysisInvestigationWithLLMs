#!/bin/bash

# Define arrays of keywords and date ranges
keywords=(
  "software fail"
  "software hack" 
  "software bug" 
  "software fault" 
  "software error" 
  "software exception" 
  "software crash" 
  "software glitch"
  "software defect" 
  "software incident" 
  "software flaw" 
  "software mistake" 
  "software anomaly" 
  "software side effect"
)

start_years=(2020)
end_years=(2020)
start_months=(9)
end_months=(10)

# Iterate through all combinations of keywords, years, and months
for keyword in "${keywords[@]}"
do
  for (( i=0; i<${#start_years[@]}; i++ ))
  do
    start_year=${start_years[$i]}
    end_year=${end_years[$i]}
    
    for (( j=0; j<${#start_months[@]}; j++ ))
    do
      start_month=${start_months[$j]}
      end_month=${end_months[$j]}
    
      # Execute the command with the current keyword and date range
      docker compose -f local.yml run --rm django python -m failures scrape --sources 'wired.com' 'nytimes.com' --keyword "$keyword" --start-year $start_year --end-year $end_year --start-month $start_month --end-month $end_month
    done
  done
done