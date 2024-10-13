import flask

import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://coe:CoEpasswd@localhost:5432/coedb"
)

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()

    # for row in notes.fetchall():
    #     print("id :",row.id,
    #           "\ntitle :",row.title,
    #           "\ndescription :",row.description,
    #           "\ntags :",[x.name for x in row.tags],
    #           "\ncreated_date :",row.created_date,
    #           "\nupdated_date :",row.updated_date,
    #           "\n----------------------"
    #           )

    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def notes_edit(note_id):
    db = models.db
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalar()

    form = forms.NoteForm()
    if form.validate_on_submit():
        note.title = form.title.data
        note.description = form.description.data
        oldTags = [x.name for x in note.tags]
        note.tags.clear()

        for tag_name in form.tags.data:
            tag = (
                db.session.execute(
                    db.select(models.Tag).where(models.Tag.name == tag_name)
                )
                .scalars()
                .first()
            )
            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)
            note.tags.append(tag)

        for i in range(len(oldTags)):
            tag = (
                db.session.execute(
                    db.select(models.Tag).where(models.Tag.name == oldTags[i])
                )
                .scalars()
                .first()
            )
            notes = db.session.execute(
                db.select(models.Note).where(models.Note.tags.any(id=tag.id))
            ).scalars()
            if not notes.fetchall():
                db.session.delete(tag)
                db.session.commit()
        db.session.commit()
        return flask.redirect(flask.url_for("index"))

    if note:
        form.title.data = note.title
        form.description.data = note.description
        form.tags.data = [x.name for x in note.tags]

    return flask.render_template(
        "note-edit.html",
        form=form,
    )


@app.route("/notes/delete/<int:note_id>", methods=["GET"])
def delete_note(note_id):
    db = models.db
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalar()

    # print("id :",note.id,
    #           "\ntitle :",note.title,
    #           "\ndescription :",note.description,
    #           "\ntags :",[x.name for x in note.tags],
    #           "\ncreated_date :",note.created_date,
    #           "\nupdated_date :",note.updated_date,
    #           "\n----------------------"
    #           )
    if note:
        db.session.delete(note)
        db.session.commit()
        for i in range(len(note.tags)):
            tag = (
                db.session.execute(
                    db.select(models.Tag).where(models.Tag.name == note.tags[i].name)
                )
                .scalars()
                .first()
            )
            notes = db.session.execute(
                db.select(models.Note).where(models.Note.tags.any(id=tag.id))
            ).scalars()
            if not notes.fetchall():
                db.session.delete(tag)
                db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )


if __name__ == "__main__":
    app.run(debug=True)
