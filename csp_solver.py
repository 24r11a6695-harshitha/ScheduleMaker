class StudySchedulerCSP:
    def __init__(self, topics, available_days, max_hours_per_day, max_hrs_per_subject_per_day=2):
        self.blocks = []
        # Flatten topics into 1-hour session blocks
        for orig_idx, item in enumerate(topics):
            topic_name = item["topic"]
            total_hrs = int(item["hours"])
            time_str = item["time"]
            
            for part in range(1, total_hrs + 1):
                self.blocks.append({
                    "orig_idx": orig_idx,
                    "topic": topic_name,
                    "part": part,
                    "total_parts": total_hrs,
                    "time": time_str,
                    "hours": 1
                })
                
        self.available_days = available_days
        self.max_hours_per_day = max_hours_per_day
        self.max_hrs_per_subject_per_day = max_hrs_per_subject_per_day

    def is_consistent(self, block_idx, day, assignment):
        current_block = self.blocks[block_idx]
        
        # Check total daily hour limit
        current_day_total_hours = sum(
            1 for idx, assigned_day in assignment.items() 
            if assigned_day == day
        )
        if current_day_total_hours + 1 > self.max_hours_per_day:
            return False

        # Limit max hours per subject per day to ensure subject mixing
        subject_hours_today = sum(
            1 for idx, assigned_day in assignment.items()
            if assigned_day == day and self.blocks[idx]["topic"] == current_block["topic"]
        )
        if subject_hours_today + 1 > self.max_hrs_per_subject_per_day:
            return False

        # Maintain sequential ordering for session parts
        if current_block["part"] > 1:
            prev_block_idx = block_idx - 1
            if prev_block_idx in assignment:
                prev_day = assignment[prev_block_idx]
                if self.available_days.index(day) < self.available_days.index(prev_day):
                    return False

        return True

    def backtrack(self, assignment=None):
        if assignment is None:
            assignment = {}

        if len(assignment) == len(self.blocks):
            return assignment

        unassigned = [i for i in range(len(self.blocks)) if i not in assignment]
        var = unassigned[0]

        for day in self.available_days:
            if self.is_consistent(var, day, assignment):
                assignment[var] = day
                result = self.backtrack(assignment)
                if result is not None:
                    return result
                del assignment[var]

        return None