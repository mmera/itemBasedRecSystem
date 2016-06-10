"""
Simple item-item collaborative filtering restaurant recommendation engine built using the yelp dataset. 
ver 1.0 - Works for states AZ, NV, NC.
For more information on the dataset used please visit http://yelp.com/dataset_challenge
@author Marco Mera
"""
import pandas as pd
import numpy as np
import sys
import random
from math import sqrt

def square_rooted(x):
	'''
	Helper function for cosine similarity 
	'''
	return sqrt(sum([a*a for a in x]))


def cosine_similarity(x,y):
	'''
	The distance metric used to determine similarity between item vectors
	'''
	numerator   = sum(a*b for a,b in zip(x,y)) 
	denominator = square_rooted(x) * square_rooted(y)
	return 1 - numerator/float(denominator)

def process_business_data(data):
	'''
	The yelp dataset consists of millions of businesses not limited to 
	restaurants. With this function I process the data by eliminating 
	the businesses that aren't restaurants as well as restaurants with a 
	rating less than 3.5 and a total review count less than 50.
	'''
	business = pd.read_csv(data,usecols=(15,20,23,36,38,61))
	size = business.shape[0]
	drop_index = []
	#If a row in the DF is not a restaurant its index is added to a list to use later for dropping the rows
	for i in range(size):
		if "Restaurants" not in business["categories"][i]:
			drop_index.append(i)
	business = business.drop(business.index[[drop_index]])#Use the indexes to drop rows
	business = business[business['review_count'] >= 50]
	business = business[business['stars'] >= 3.5]
	return business


def get_state_df(businessData,state):
	'''
	This function narrows down the DF to a particular state.
	'''
	states = [s for s in set(business.state.values) if business[business['state']==s].shape[0]>200] # A list of states who have over 200 restaurants
	if state in states:
		return businessData[businessData['state']== state]
	else:
		print "Sorry that state is not supported yet! Will use the default: NC "
		return businessData[businessData['state']=='NC'] #default

def get_table(stateDF):
	'''
	Function to cross reference the reviews DF with the state DF in order to produce a pivot 
	table that contains the (ratings X users), with the NA values set to zero.
	'''
	reviews = stars[stars['business_id'].isin(stateDF['business_id'].values)]
	table   = reviews.pivot_table(index='business_id', columns='user_id', values='stars').fillna(0)
	return table


def get_matrix(table):
	'''
	Function to convert the Pandas table to a matrix (Numpy array). It also serves to remove the users that
	have reviewed less than '5%' of the businesses.
	'''
	matrix = table.values.T
	size   = matrix.shape[0]
	n      = matrix.shape[1]
	index  = []
	for i in range(size):
		if np.count_nonzero(matrix[i]) < int(n*.05): #If that user has reviewed less than 5% of n restaurants then we're going to drop that user
			index.append(i)
	matrix = np.delete(matrix,index,axis=0) 
	return matrix


def get_restaurant_names(table,state_df):
	'''
	This function grabs the restaurant names from a table and puts them in a list.  
	'''
	business_ids     = table.T.columns	
	restaurant_names = []
	for i in range(len(business_ids)):
		#This row cross references the business_ids in the pivot table generated with the state DF to get the actual name of the business.      
		restaurant_names.append((state_df.loc[state_df['business_id'] == business_ids[i]]).name.values[0]) 
	return restaurant_names


def list_restaurant_options(matrix,restaurant_names):
	'''
	Function that searches the matrix for the 5 restaurants with the most reviews and prints those. 
	It also prints 5 random restaurants. 
	'''
	restaurant_ratings = matrix.T 
	size    = restaurant_ratings.shape[0] 
	maxList =[np.count_nonzero(row) for row in restaurant_ratings] #List of counts of reviews for each row(restaurant)
	indexes =[]
	rands   = random.sample(range(0,size-1),5) #A list of five random ints to be used for printing random restaurants
	
	#This loop appends the index of the row with the most reviews to a list of indexes
	for i in range(5):
		temp = maxList.index(max(maxList))
		indexes.append(temp)
		maxList[temp]=0 # We reset the to review count (to zero) so it won't be counted in the next iteration 
	
	print "Here are the top 5 most popular restaurants in the area:"
	print "-------------------------------------------------------"
	for restaurant in indexes:
		print restaurant_names[restaurant]
		print"**"
	print "\nFor more options, here is a list of five random restaurants:"
	print "-----------------------------------------------------------"
	for restaurant in rands:
		print restaurant_names[restaurant]
		print"**"



def print_top_k_restaurants(matrix,restaurant_names,query_restaurant,k):
	"""

	"""
	restaurant_ratings = matrix.T

	if query_restaurant == "random":
		print "\nChose random I see...I too like to live dangerously!"
		rest_index = random.randint(0,restaurant_ratings.shape[0]) #We get an index for a random restaurant in the matrix 
	else:
		try:  
			rest_index = restaurant_names.index(query_restaurant) #We attempt to find the restaurant the user is querying 
		except ValueError: #Otherwise we just use a random index 
			print "\nSorry that restaurant was not found! Will use a random restaurant instead :)"
			rest_index = random.randint(0,restaurant_ratings.shape[0])


	query_restaurant_rating = restaurant_ratings[rest_index] #We get the vector of user ratings for that restaurant 
	distances = [cosine_similarity(query_restaurant_rating,restaurant) for restaurant in restaurant_ratings] # We compute the distances between that restaurant and all the other restaurants in the matrix
	indexes   = []
	#Compiles a list of the k restaurants(indexes) with the smallest distance to the query restaurant 
	for i in range(k+1):
		temp = distances.index(min(distances))
		indexes.append(temp)
		distances[temp]=1 # Reset the distance (to one) so that it won't be counted in the next iteration
	print "\nGreat! Based on the selected restaurant: %s" % restaurant_names[rest_index]
	print "\nHere are your top %d recommended restaurants:" % k
	print "---------------------------------------------"
	for restaurant in indexes[1:]: #We don't want to count the smallest distance since it will be the query restaurant itself 
		print restaurant_names[restaurant]
		print"**"

#Read files from command line 
reviews    = sys.argv[1]
businesses = sys.argv[2]

print "\n**************************************"
print "* Welcome to Restaurant Recommender! *"
print "**************************************"

state = raw_input("\nWhat state will you be traveling to?\nThese are your options: ['NC', 'WI', 'QC', 'PA', 'AZ', 'NV'] ")
print "\nOne moment please while we fire up some recommendations for you!\n"
stars    = pd.read_csv(reviews, usecols=(0,4,6))
business = process_business_data(businesses)

state_df = get_state_df(business, state)
table    = get_table(state_df)
matrix   = get_matrix(table)
restaurant_names = get_restaurant_names(table, state_df)

run = 'y' #flag to keep running program, anything else terminates program 
while run == 'y':
	list_restaurant_options(matrix, restaurant_names)
	selected_restaurant = raw_input("\nWhat restaurant are you curious about? (You can also type "'"random"'"): ")
	k = raw_input("\nHow many restaurants do you want recommended to you? ")
	print_top_k_restaurants(matrix,restaurant_names,selected_restaurant,int(k))
	run = raw_input("\nWould you like to search for a different restaurant? [y/n] ")
	print 










