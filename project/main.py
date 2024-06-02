from flask import (
  Blueprint, render_template, request, 
  flash, redirect, url_for, send_from_directory, 
  current_app, make_response
)
from .models import Photo
from sqlalchemy import asc, text
from . import db
import os

main = Blueprint('main', __name__)

# This is called when the home page is rendered. It fetches all images sorted by filename.
@main.route('/')
def homepage():
  photos = db.session.query(Photo).order_by(asc(Photo.file))
  return render_template('index.html', photos = photos)

@main.route('/uploads/<name>')
def display_file(name):
  return send_from_directory(current_app.config["UPLOAD_DIR"], name)

# Upload a new photo
@main.route('/upload/', methods=['GET','POST'])
def newPhoto():
  if request.method == 'POST':
    file = None
    if "fileToUpload" in request.files:
      file = request.files.get("fileToUpload")
    else:
      flash("Invalid request!", "error")

    if not file or not file.filename:
      flash("No file selected!", "error")
      return redirect(request.url)

    filepath = os.path.join(current_app.config["UPLOAD_DIR"], file.filename)
    file.save(filepath)

    newPhoto = Photo(name = request.form['user'], 
                    caption = request.form['caption'],
                    description = request.form['description'],
                    file = file.filename)
    db.session.add(newPhoto)
    flash('New Photo %s Successfully Created' % newPhoto.name)
    db.session.commit()
    return redirect(url_for('main.homepage'))
  else:
    return render_template('upload.html')

# This is called when clicking on Edit. Goes to the edit page.
@main.route('/photo/<int:photo_id>/edit/', methods = ['GET', 'POST'])
def editPhoto(photo_id):
  editedPhoto = db.session.query(Photo).filter_by(id = photo_id).one()
  if request.method == 'POST':
    if request.form['user']:
      editedPhoto.name = request.form['user']
      editedPhoto.caption = request.form['caption']
      editedPhoto.description = request.form['description']
      db.session.add(editedPhoto)
      db.session.commit()
      flash('Photo Successfully Edited %s' % editedPhoto.name)
      return redirect(url_for('main.homepage'))
  else:
    return render_template('edit.html', photo = editedPhoto)


# This is called when clicking on Delete. 
@main.route('/photo/<int:photo_id>/delete/', methods = ['GET','POST'])
def deletePhoto(photo_id):
  fileResults = db.session.execute(text('select file from photo where id = ' + str(photo_id)))
  filename = fileResults.first()[0]
  filepath = os.path.join(current_app.config["UPLOAD_DIR"], filename)
  os.unlink(filepath)
  db.session.execute(text('delete from photo where id = ' + str(photo_id)))
  db.session.commit()
  
  flash('Photo id %s Successfully Deleted' % photo_id)
  return redirect(url_for('main.homepage'))


# This is called when clicking on Comment.
@main.route('/<user>/photo/<int:photo_id>/comment/add', methods = ['POST'])
def new_comment(photo_id):
  commented_photo = db.session.query(Photo).filter_by(id = photo_id).one()  
  if request.method == 'POST':
    user_input = request.form['comment']
    for word in word_filter:  #This checks user input against either a dictionary or a database of banned terms
      if word in user_input:
        flash('Your comment may violate our community guidelines, please reconsider or change your wording')
        return redirect(url_for(commented_photo))
      return user_input
    new_comment = Comment(name = request.form['user'], comment = user_input)
    db.session.add(new_comment)
    db.session.commit()
    flash('Comment Successfully  Added %s' % commented_photo.name)
    return redirect(url_for('main.photo'))
  else:
    return render_template('comment.html', photo = commented_photo)

# This is called when clicking on Edit Comment.
@main.route('/<user>/photo/<int:comment_id>/comment/edit', methods = ['PUT'])
def edit_comment(comment_id):
  edited_comment = db.session.query(Photo).filter_by(id = comment_id).one()  
  if request.method == 'PUT':
    user_input = request.form['comment']
    for word in word_filter:  #This checks user input against either a dictionary or a database of banned terms
      if word in user_input:
        flash('Your comment may violate our community guidelines, please reconsider or change your wording')
        return redirect(url_for('main.photo'))
      return user_input
    edited_comment.name = request.form['user']
    edited_comment.comment = user_input
    db.session.add(edited_comment)
    db.session.commit()
    flash('Comment Successfully Changed %s' % edited_comment.name)
    return redirect(url_for('main.homepage'))
  else:
    return render_template('comment.html', comment = edited_comment)
  

# This is called when clicking on Search.
@main.route('/search', methods = ['GET'])
def search():
  user_input = request.args.get('user_input')
  if user_input and user_input.isalnum():  #Prevents injection by only allowing alphanumeric characters.
    result = db.session.query(Photo).filter_by(handle = user_input).all()
    return render_template('index.html', photos = result)
  else:
    flash('Please only input alphanumeric charachters!')
    return redirect(url_for('main.homepage'))
  
  
