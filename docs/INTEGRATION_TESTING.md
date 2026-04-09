# Integration Testing – Feature A

## Test Case 1 – Create Assignment with Rich Text
- Add bold text
- Add bullet list
- Save
- Verify formatting renders correctly

## Test Case 2 – Upload Valid PDF
- Upload 2MB PDF
- Verify success message
- Verify download link appears
- Download works

## Test Case 3 – Reject Non-PDF
- Upload .txt file
- Expect error

## Test Case 4 – Reject >10MB
- Upload 12MB PDF
- Expect error

## Test Case 5 – Edit Assignment
- Modify rich text
- Replace attachment
- Verify updates

## Test Case 6 – Delete Attachment
- Remove file
- Verify link disappears

## Test Case 7 – Authentication
- Attempt upload as student
- Expect rejection
