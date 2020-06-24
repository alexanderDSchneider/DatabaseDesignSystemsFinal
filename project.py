import pymongo
import uuid
import hashlib
from bson import ObjectId


#for officers to see all tickets that are yet to be paid
#can see if they are "repeat offenders" and need to be contacted
def view_all_unpaid_tickets(mydb):

    #connect to tables
    peoplecoll = mydb["people"]

    #view all unpaid ticket arrays
    for x in peoplecoll.find({}, {"_id": 0, "name": 1, "unpaid_tickets": 1}):    
        print(x)

#for admin to view and clear contested ticket
#shows one at a time and they have to be cleared one at a time
def view_contested_ticket(mydb):

    #connect to tables
    peoplecoll = mydb["people"]
    ticketcoll = mydb["tickets"]
  
    #find the contested tickets
    #cant figure out why but i have to set a cariable to a boolean to  pass it
    true = True
    query = {"contested": { "$eq":true}}
    find = {"_id": 1, "reason": 1, "contest_reason": 1}
    
    try:  
        tickets = ticketcoll.find_one(query,find)

        for x in tickets:
            
            ticket_id = tickets["_id"]
            reason = tickets["reason"]
            reason_contested = tickets["contest_reason"]

        printing = "TicketID: " + ticket_id + " Reason Given: " + reason +  " Reason contested: " + reason_contested
        print(printing)     
                
        decision = input("Does the ticket still stand(y/n): ")

        if decision == 'n':
            #remove from the unpaid ticket array
            #find the ticket in a persons unpaid ticket array
            query = {"unpaid_tickets":{"$in":[ticket_id]}}
            find = {"_id": 1, "name": 1,"contact_info": 1}
            person = peoplecoll.find_one(query, find)
            
            
            for x in person:
                name = person["name"]
                owner_id = person["_id"]
                contact_info = person["contact_info"]

            #copy ticket id to past tickets then remove from unpaid
            update_at = {"_id": owner_id}
            
            data = {"$push": {"past_tickets": ticket_id }}
            peoplecoll.update_one(update_at, data)
            
            data = {"$pull": {"unpaid_tickets": ticket_id }}
            peoplecoll.update_one(update_at, data)

            #i cant get booleans to pass any other way besides setting them to a variable                
            false = False
            true = true
            
            query = {"_id": ticket_id}
            is_contested = {"$set": {"contested": false}}

            #set the contested boolean to false so that it is no longer brought up in search
            ticketcoll.update_one(query, is_contested)
            
            #set a boolean to show that the ticket has been withdrawn in ticket info
            update = {"$set": {"withdrawn": true}}
            ticketcoll.update_one(query, update)
            
            #set as paid so it no longer shows as an unpaid ticket in other searches
            ticketcoll.update_one(query, {"$set": {"paid": true}})

            print("Ticket withdrawn")
            print("Contact individual to inform them of the results of the review ")
            print(name)
            print(contact_info)
                        
        else:
            #find the ticket in a persons unpaid ticket array
            query = {"unpaid_tickets":{"$in":[ticket_id]}}
            person = peoplecoll.find_one(query,{"_id": 1, "name": 1,"contact_info": 1})
            
            for x in person:
                name = person["name"]
                contact_info = person["contact_info"]

            false = False

            query = {"_id": ticket_id}
            is_contested = {"$set": {"contested": false}}

            #set the contested boolean to false so that it is no longer brought up in search
            ticketcoll.update_one(query, is_contested)
            #set a boolean to show that the ticket has been withdrawn in ticket info
            ticketcoll.update_one(query, {"$set": {"withdrawn": false}})

            print("Ticket not withdrawn")
            print("Contact individual to inform them of the results of the review ")
            print(name)
            print(contact_info)
            
    #if not found catch nonetype exception and try again
    except (TypeError):
        
        print("No contested tickets")
    
    
#method for somemone to challenge their ticket with an administrator 
def contest(mydb):
    
    #connect to tables
    ticketcoll = mydb["tickets"]

    ticket_id = input('Enter the id on the ticket: ')
    reason = input('Enter why you feel the ticket is unjust: ')

    try:

        query = {"_id": ticket_id}
        #find ticket by id and return ticket contested Boolean
        ticket = ticketcoll.find_one(query,{ "contested": 1})
       
        #for some reason i cant get it to work with is_contested = {"$set": {"contested": True}}
        #so i set it to a variable                             
        true = True
            
        is_contested = {"$set": {"contested": true}}

        #set the contested boolean to true
        ticketcoll.update_one(query, is_contested)
        #reason is not a default field for ticket, it needs to be added to it
        ticketcoll.update_one(query, {"$set": {"contest_reason": reason}})
        
        print("Your ticket has been submitted for review")    

    except (TypeError):        
         print("Data entered incorrectly/not found try again")
    

#method to pay for tickets
def pay_ticket(mydb):

    #connect to tables
    #officercoll = mydb["officer"]
    peoplecoll = mydb["people"]
    ticketcoll = mydb["tickets"]

    ticket_id = input('Enter the id on the ticket: ')

    try:
        #find the ticket in a persons unpaid ticket array
        query = {"unpaid_tickets":{"$in":[ticket_id]}}
        person = peoplecoll.find_one(query,{"_id": 1, "name": 1})
        
        
        for x in person:
            name = person["name"]
            owner_id = person["_id"]

        #copy ticket id to paid then remove from unpaid
        update_at = {"_id": owner_id}
        
        data = {"$push": {"past_tickets": ticket_id }}
        peoplecoll.update_one(update_at, data)
        
        data = {"$pull": {"unpaid_tickets": ticket_id }}
        peoplecoll.update_one(update_at, data)

        
        query = {"_id": ticket_id}
        find = { "paid": 1}
        ticket = ticketcoll.find_one(query,find)       

        #for some reason it doesnt work in is_paid if it is True so it is set to a variable here
        true = True
        #find ticket in ticket collection and update it  
        is_paid = {"$set": {"paid": true}}
        #change boolean status for if ticket is paid
        ticketcoll.update_one(query, is_paid)
        for x in person:
            name = person["name"]
            owner_id = person["_id"]
        
        print ("Thank you, ", name)

        
    #if not found catch nonetype exception and try again
    except (TypeError):
        print("Data entered incorrectly/not found try again/or the ticket has already has been paid")
    

#method to insert tickets to db
def enter_ticket(mydb):

    #connect to tables
    officercoll = mydb["officer"]
    vehichlecoll = mydb["vehicles"]
    peoplecoll = mydb["people"]
    ticketcoll = mydb["tickets"]

    ticket_id = input("Enter the ticket id: ")
    officer_id = input("Enter the officer id:")
    plate = input("Plate number: ")
    location = input("Enter the location: ")
    reason = input("Reason: ")
    date = input("Date(dd/mm/yyyy): ")


    #i wanted to see if i could find the person to attribute the ticket to
    #by finding the plate from the person collection rather than having the person_id attached to the vehicle
    #as an attempt to treat the vehicles array as what would be a junction table in a relational db
    #find the person to add the ticket to by vehicle id

    try:
        #find in the vehicles array
        query = {"vehicles":{"$in":[plate]}}
        person = peoplecoll.find_one(query,{"_id": 1, "name": 1})
        
        for x in person:
            name = person["name"]
            owner_id = person["_id"]  

        print ("Owner of vehicle: ", name)
    #if not found catch nonetype exception and try again
    except (TypeError):
        print("Data entered incorrectly/not found try again")
    

    data_dict = {"_id": ticket_id, "officer_id": officer_id, "plate": plate, "location": location,
                 "reason": reason, "date": date, "paid": False, "contested": False}

    try:
        #insert full ticket into ticket collection        
        ticketcoll.insert_one(data_dict)
        #insert ticketid into 
        officercoll.update_one({"_id": officer_id}, {"$push": {"tickets_written": ticket_id}})
                               
        peoplecoll.update_one({"_id": owner_id}, {"$push": {"unpaid_tickets": ticket_id }} )
    #if duplicate prompt     
    except pymongo.errors.DuplicateKeyError:
        print("Duplicate ticketID try again")
        

#main menu
def menu(mydb):

    #for passing database connection info to other methods
    mydb = mydb

    menu_select = 0

    print('Enter 1: To pay a ticket.')
    print('Enter 2: To contest a ticket')
    print('Enter 3: To login as an officer.')
    print('Enter 4: To login as an admin.')
    print('Enter 5: To exit')

    try:
        menu_select = int(input('Enter Selection: '))
        
        if menu_select == 1:
            pay_ticket(mydb)
            menu(mydb)
        elif menu_select == 2:
            contest(mydb)
            menu(mydb)
        elif menu_select == 3:
            officer_login(mydb)
        elif menu_select == 4:
            admin_login(mydb)
            admin_menu(mydb)
        elif menu_select == 5:
            menu_select = 5

    except:
        print("Invalid input try again")
        menu(mydb)

#officer menu
def officer_menu(mydb):

    #for passing database connection info to other methods
    mydb = mydb

    menu_select = 0

    print('Enter 1: To enter a ticket.')
    print('Enter 2: To see tickets that are unpaid and owners.')
    print('Enter 3: To login as an admin.')
    print('Enter 4: To exit')

    try:
    
        menu_select = int(input('Enter Selection: '))
        
        if menu_select == 1:
            enter_ticket(mydb)
            officer_menu(mydb)
        elif menu_select == 2:
            view_all_unpaid_tickets(mydb)
            officer_menu(mydb)
        elif menu_select == 3:
            admin_login(mydb)
        elif menu_select == 4:
            menu_select = 4

    except:
        print("Invalid input try again")
        officer_menu(mydb)

#admin menu
def admin_menu(mydb):

    #for passing database connection info to other methods
    mydb = mydb

    menu_select = 0

    print('Enter 1: To enter a ticket.')
    print('Enter 2: To see tickets that are unpaid and owners.')
    print('Enter 3: To add an officer')
    print('Enter 4: To remove an officer')
    print('Enter 5: To tranfer an officer to another deparmtent')
    print('Enter 6: To view contested tickets')
    print('Enter 7: To view your departments contacts list')
    print('Enter 8: To exit')

    try:
        
        menu_select = int(input('Enter Selection: '))
    
        if menu_select == 1:
            enter_ticket(mydb)
            admin_menu(mydb)
        elif menu_select == 2:
            view_all_unpaid_tickets(mydb)
            admin_menu(mydb)
        elif menu_select == 3:
            add_officer(mydb)
            admin_menu(mydb)
        elif menu_select == 4:
            remove_officer(mydb)
            admin_menu(mydb)
        elif menu_select ==5:
            transfer(mydb)
            admin_menu(mydb)
        elif menu_select ==6:
            view_contested_ticket(mydb)
            admin_menu(mydb)
        elif menu_select ==7:
            contact_info(mydb)
            admin_menu(mydb)
        elif menu_select ==8:
            menu_select = 8

    except:
        print("Invalid input, try again.")
        


#method so that an admin can see the contact information for all of the officers in their department
def contact_info(mydb):

    #connect to tables
    officercollection = mydb["officer"]
    admincollection = mydb["admin"]

    try:
        admin_id = input("Enter your admin id: ")
        query = {"_id": admin_id}
        find = {"supervise": 1}
        admin = admincollection.find_one(query, find)
        #returns an array of officer ids
        for x in admin:
            supervise = admin["supervise"]

        #iterate over the returned list and print the information from each officers contact info 
        i = 0
        print("Department contact info: ")
        while i < len(supervise): 
            officer_id = supervise[i]

            #print the array of officer contact info from the officer collection
            query = {"_id": officer_id}
            find = {"name": 1, "contact_info": 1}
            officer = officercollection.find_one(query, find)

            name = officer["name"]
            contact = officer["contact_info"]
            print(name + contact)
            i = i + 1
        
    except (TypeError):
            print("Data entered incorrectly/not found try again")


#admin transfer officer to another department
def transfer(mydb):

    #connect to database
    officercollection = mydb["officer"]
    admincollection = mydb["admin"]
    officer_id = input("Enter the id of the officer to transfer: ")
    
    
    query = {"_id": officer_id}
    find = {"name": 1, "dept": 1}
    #find officer to tranfser
    officer = officercollection.find_one(query, find)
    for x in officer:
        name = officer["name"]
        dept = officer["dept"]
    
    print("Officer", name)
    print("Current department: " + dept)
    
    new_dept = input("Enter department to transfer to: ")

    #prevent from transfering officer to current department
    if new_dept != dept:

        try:
            #put in new admins department array
            change_at = {"dept": new_dept}
            change ={"$push": {"supervise": officer_id }}
            admincollection.update_one(change_at, change)
            
            #remove from old admins department array
            change_at ={"dept": dept}
            change = {"$pull": {"supervise": officer_id }} 
            admincollection.update_one(change_at, change)
            
            #update department in officer collection
            change_at = {"_id": officer_id}
            change = {"$set": {"dept": new_dept}}
            officercollection.update_one(change_at, change)
        except (TypeError):
            print("Data entered incorrectly/not found try again")

    else:
        print("Cannot transfer to current department, try again.")

           
#login function for officer
def officer_login(mydb):

    #try catch catches invalid username
    try:
        officer_id = input("Enter your id: ")
        password = input("Enter your password: ")

        #connect to officer table
        officercollection=mydb["officer"]
        
        salt = ''      #if db does not find value for salt or hash, makes it so if to_compare == str(user_hash) is to_compare == 0
        user_hash = ''

        query = {"_id": officer_id}
        find = {"salt": 1, "hash": 1}
        
        credential = officercollection.find_one(query,find)

        #fetch salt and hash
        for x in credential:
            salt = credential["salt"]
            user_hash = credential["hash"]

        #add entered password to salt to compare
        salt = str(salt)
        to_encode = password + salt

        result_hash = hashlib.sha256(to_encode.encode())
        to_compare = result_hash.hexdigest()
        
        #if tocompare is == to the fetched user data login is successful    
        if to_compare == str(user_hash):
            print('Officer Login Successful')
            officer_menu(mydb)
        else:
            print('Officer Login Failed')
            menu(mydb)

    except (TypeError):
            print("Invalid username please try again")
            menu(mydb)
            

#login function for admin
def admin_login(mydb):

    #try catch to handle invalid username
    try:
        officer_id = input("Enter your id: ")
        password = input("Enter your password: ")

        #connect to admin table
        officercollection=mydb["admin"]
        
        salt = ''      #if db does not find value for salt or hash, makes it so if to_compare == str(user_hash) is to_compare == 0
        user_hash = ''

        query = {"_id": officer_id}
        
        credential = officercollection.find_one(query,{"salt": 1, "hash": 1})
        
        for x in credential:
            salt = credential["salt"]
            user_hash = credential["hash"]

        salt = str(salt)
        to_encode = password + salt

        result_hash = hashlib.sha256(to_encode.encode())
        to_compare = result_hash.hexdigest()
      
        if to_compare == str(user_hash):
            print('Admin Login Successful')
            admin_menu(mydb)
        else:
            print('Admin Login Failed')
            menu(mydb)

    except (TypeError):
            print("Invalid username try again")
            menu(mydb)
        

#salt and hash password
def generate_credentials(officer_id, password):

    salt = uuid.uuid4()
    salt = str(salt)
    to_encode = password + salt
    officer_hash = hashlib.sha256(to_encode.encode())

    return(salt, officer_hash.hexdigest())


#connecting people to vehicles en masse for test
def register_vehicle(mydb):

    #connect to table
    peoplecollection = mydb["people"]
    vehiclecollection = mydb["vehicles"]


    #go through all people and add a vehicle to their vehicle array
    for x in peoplecollection.find({},{"_id": 1, "name": 1, "vehicles": 1}):
        print(x)        
        name = x["name"]
        owner_id = x["_id"]
        plate  = input("Enter plate no: ")
        print(owner_id)
        peoplecollection.update_one({"_id": owner_id}, {"$push": {"vehicles": plate }} )
        
        
#adding vehicles for testing
def add_vehicle(mydb):
    
    #connect to table
    mycollection = mydb["vehicles"]
    plate = input("Liscense plate: ")
    make = input("Enter the make: ")
    model = input("Enter the model: ")
    
    data_dict = {"_id": plate, "make": make, "model": model}
    x = mycollection.insert_one(data_dict)
       

#for adding people for testing 
def add_people(mydb):

    #Specify the table
    mycollection = mydb["people"]
      
    fname = input("Enter first name: ")
    lname = input("Enter last name: ")
    email = input("Enter email: ")
    phone = input("Enter phone: ")
    address = input("Enter the address: ")
        
    #put input into a dictionary
    data_dict = { "name": [fname, lname], "contact_info": [email, phone, address], "vehicles": [], "past_tickets": [], "unpaid_tickets": []}
    #data_dict = { "name": [fname, lname]}
    #insert data into table
    x = mycollection.insert_one(data_dict)
    
#admin function to add officer
def add_officer(mydb):       

    officercollection = mydb["officer"]
    peoplecollection = mydb["people"]
    perid = input("Enter the persons id: ")

    #find person by id
    query = {"_id": ObjectId(perid)}

    #fetch person id, name and contact info for new officer
    find = {"_id": 1, "name": 1, "contact_info": 1}

    try:
        person = peoplecollection.find(query,find)
        print(person)

        #get the information you want duplicated in officer from people   
        for x in person:
            print(x)
            name = x["name"]
            personid = x["_id"]
            contact_info = x["contact_info"]
            print(name)

        officer_id = input("Enter the officer ID: ")
        dept = input("Assign to a department: ")  
        password = input("Input the password: ")

        #pass username and password to salt and hash function
        credentials = generate_credentials(officer_id, password)
        salt = credentials[0]
        officer_hash = credentials[1]
        
        data_dict = {"_id": officer_id, "person_id": personid, "name": name,
                     "contact_info": contact_info,"dept": dept, "salt": salt, "hash": officer_hash,
                     "tickets_written": []}

        officercollection.insert_one(data_dict)

    except (TypeError):
            print("Data entered incorrectly/not found try again")
        
#admin method to remove an officer        
def remove_officer(mydb):

    #connect to table
    officercollection = mydb["officer"]

    #query to find document to remove
    officer_id = input("What officer to remove by ID: ")

    try:
        query = {"_id": officer_id}    
    
        officercollection.delete_one(query)
    except (TypeError):
            print("Data entered incorrectly/not found try again")

    print("removed")
    
    
def main():

    #connection string
    client = pymongo.MongoClient("mongodb+srv://alex:putty1562@cluster0-tewlq.mongodb.net/test?retryWrites=true&w=majority")

    #Specify what db we are accessing
    mydb = client["ticket_system"]

    menu(mydb)
      
if __name__ == '__main__':  # for import
    main()    
