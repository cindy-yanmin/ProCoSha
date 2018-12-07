# ProCoSha

PriCoSha should support the following use cases:

1. View public content: PriCoSha shows the user the item_id, email_post, post_time, file_path, and item_name of public content items that were posted within the last 24 hours. (If you prefer, you can include this with use case (3) below).

2. Login: The user enters e-mail and password. PriCoSha checks whether the hash of the password matches the stored password for that e-mail. If so, it initiates a session, storing the e-mail and any other relevant data in session variables, then goes to the home page (or provides some mechanism for the user to select their next action.) If the password does not match the stored password for that e-mail (or no such user exists) PriCoSha informs the user that the the login failed and does not initiate the session.
The remaining features require the user to be logged in.

3. View shared content items and info about them: PriCoSha shows the user the item_id, email_post, post_time, file_path, and item_name of content items that are visible to the her, arranged in reverse chronological order. (Optionally, include a link to an actual content item or a way to display it.) Along with each content item there should be a way for the user to see further
information, including
a. first name and last name of people who have been tagged in the content item (taggees), provided that they have accepted the tags (Tag.status == true)
b. Ratings of the content item

4. Manage tags: PriCoSha shows the user relevant data about content items that have proposed tags of this user (i.e. user is the taggee and status false.) User can choose to accept a tag (change status to true), decline a tag (remove the tag from Tag table), or not make a decision (leave the proposed tag in the table with status == false.)

5. Post a content item: User enters the relevant data (and optionally, a link to a real content item) and a designation of whether the content item is public or private. PriCoSha inserts data about the content item (including current time, and current user as owner) into the Content table. If the content item is private, PriCoSha gives the user a way to designate FriendGroups that the user belongs to with which the Photo is shared.

6. Tag a content item: Current user, who we’ll call x, selects a content item that is visible to her and proposes to tag it with e-mail y

7. Add friend: User selects an existing FriendGroup that they own and provides first_name and last_name. PriCoSha checks whether there is exactly one person with that name and updates the Belong table to indicate that the selected person is now in the FriendGroup. Unusual situation such as multiple people with the same name and the selected person already being in the FriendGroup should be handled gracefully.

8. Make new friend group
