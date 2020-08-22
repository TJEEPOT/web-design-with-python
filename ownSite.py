from flask import Flask, render_template, flash, redirect, request, session, abort
import os
import csv
from datetime import datetime, date, timedelta

app = Flask(__name__)

# Custom 404 page.
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


def readFile(aFile):
# read in 'aFile' 
    with open(aFile, 'r') as inFile:
        reader = csv.reader(inFile)
        List = [row for row in reader]
    return List
    
def writeFile(aList, aFile):
# write 'aList' to 'aFile' 
    with open(aFile, 'w', newline='') as outFile:
        writer = csv.writer(outFile)
        writer.writerows(aList)
    return


@app.route('/')
def home(): 
    return render_template('home.html')

## Rental System ##
@app.route('/rental')
def rental():
    rentalFile = 'static\\rental_periods.csv'
    rentalList = readFile(rentalFile)
    bookedList = []
    
    # Format the date differently for output.
    # With thanks to https://stackoverflow.com/questions/43015818/python-string-to-date
    for line in rentalList[1:]: # Skip the first line.
        dateFrom = datetime.strptime(line[0], '%Y-%m-%d') # String Parse 'From' Date.
        line[0] = dateFrom.strftime('%A, %d %B %Y') # String Format 'From' Date.

        dateTo = datetime.strptime(line[1], '%Y-%m-%d') # String Parse 'To' Date.
        line[1] = dateTo.strftime('%A, %d %B %Y') # String Format 'To' Date.
    
        # Then reformat dates for adding to build bookedList
        year = int(dateFrom.strftime('%Y'))
        month = int(dateFrom.strftime('%m'))
        day = int(dateFrom.strftime('%d'))
        dateFrom = date(year, month, day) # rebuild dateFrom as an object of ints.

        year = int(dateTo.strftime('%Y'))
        month = int(dateTo.strftime('%m'))
        day = int(dateTo.strftime('%d'))
        dateTo = date(year, month, day)

        # build list of dates, with help from https://stackoverflow.com/a/7274316
        numDatesBetween = dateTo - dateFrom
        for i in range(1, numDatesBetween.days):
            storeDate = (dateFrom + timedelta(i)).__str__() # converts date object to string
            bookedList.append(storeDate)
        print(bookedList)
    return render_template('rental.html', aList = rentalList, bList = bookedList)

@app.route('/rentalRequest', methods = ['POST'])
def rentalRequest():
# add a new rental to the rental file

    # read the rentals from file 
    rentalFile = 'static\\rental_periods.csv' 
    rentalList = readFile(rentalFile)
    
    # add the new entry, using 'values' allows dates to be parsed correctly.
    fromDate = request.values[('fromDate')]
    toDate = request.values[('toDate')] 
    name = request.form[('name')] 
    email = request.form[('email')] 

    newEntry = [fromDate, toDate, name, email,'n'] # 'n' for 'unconfirmed'.
    rentalList.append(newEntry)
    
    # save the rental list to the file 
    writeFile(rentalList, rentalFile)
    return redirect('rental') # redirect so refreshing or going back doesn't resubmit.

## Reviews system ##
@app.route('/reviews')
def reviews():
    reviewFile = 'static\\reviews.csv'
    reviewList = readFile(reviewFile)
    date = ""

    # Display the date in calender format.
    for line in reviewList[1:]:
        date = datetime.strptime(line[2], '%Y-%m-%d')
        date = date.strftime('%A, %d %B %Y')
        line[2] = date
    return render_template('reviews.html', aList = reviewList)
	
@app.route('/addReview', methods = ['POST'])    
def addReview():
    reviewFile = 'static\\reviews.csv'
    reviewList = readFile(reviewFile)

    # add the new entry
    name = request.form[('name')]
    review = request.form[('review')]

    # set date format
    date = datetime.now()
    date = date.strftime('%Y-%m-%d')

    newEntry = [name, review, date]
    reviewList.append(newEntry)

    # save the reviewList to the file
    writeFile(reviewList, reviewFile)
    return redirect('reviews')

## Admin Login System ##
@app.route('/admin', methods = ['POST', 'GET'])
def admin():
    if not session.get('logged_in'):
        return render_template('adminLogin.html')	
    else:
        rentalFile = 'static\\rental_periods.csv'
        rentalList = readFile(rentalFile)

        reviewFile = 'static\\reviews.csv'
        reviewList = readFile(reviewFile)
        return render_template('admin.html', aList = rentalList, bList = reviewList)
			
@app.route('/login', methods=['POST'])
def do_admin_login():
	if request.form['password'] == 'password' and request.form['username'] == 'admin':
		session['logged_in'] = True
		return redirect('admin')
	else:
		return render_template('403.html')
		
@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

## Admin Controls ##
@app.route('/confirmRental', methods = ['POST'])
def confirmRental():
    rentalFile = 'static\\rental_periods.csv'
    rentalList = readFile(rentalFile)

    # rental confirmation code
    confirmEntry = request.form.getlist('confirm')
    confirmEntry = list(map(int, confirmEntry)) # cast strings to ints for comparison.
    # https://stackoverflow.com/questions/7368789/convert-all-strings-in-a-list-to-int

    # go through rentalList, for each box ticked, modify the corrisponding line in the list.
    for i in confirmEntry: 
        currStr = rentalList[i] # find the relevent line (array) in rentalList.
        currStr.pop(4) # remove the last entry (confirmed y/n).
        currStr.append('y') # and replace it with a 'y'
         
    # code to deal with rental deletion
    deleteEntry = request.form.getlist('delete')
    deleteEntry = list(map(int, deleteEntry)) # cast strings to ints again
    deleteEntry = list(reversed(deleteEntry)) # reverse the list to prevent popped early entries moving the list down the index.
    for i in deleteEntry:
        rentalList.pop(i)

    writeFile(rentalList, rentalFile)
    return redirect('admin')

@app.route('/deleteComment', methods = ['POST'])
def deleteComment():
    reviewFile = 'static\\reviews.csv'
    reviewList = readFile(reviewFile)

    # build an array of entries and delete based off of checkboxes ticked.
    deleteEntry = request.form.getlist('delete')
    deleteEntry = list(map(int, deleteEntry))
    deleteEntry = list(reversed(deleteEntry))
    for i in deleteEntry:
        reviewList.pop(i)

    writeFile(reviewList, reviewFile)
    return redirect('admin')

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug = True)
