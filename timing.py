import json

# Define the fields in timingObj
fields = ["updateGameState", "renderPlayers", "renderPowerUps", "handleMovement"]

# Initialize counters for each field
counters = {field: 0 for field in fields}
timers = {field: 0 for field in fields}

# Open the file in read mode
with open("timingLog1.txt", "r") as logs:
    for line in logs:
        # Load the JSON data from the line
        timingObj = json.loads(line.strip())
        
        # Update the counters and timers for each field
        for field in fields:
            counters[field] += 1
            timers[field] += timingObj[field]
            
# Calculate the average time for each field
averages = {field: timers[field] / counters[field] for field in fields}

with open("timingAverages1.txt", "a") as logs:
    logs.write(json.dumps(averages) + '\n')

# Print the average times
# for field, average in averages.items():
#     print(f"{field}: {average}")