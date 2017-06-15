from flask import render_template
from flask_login import current_user

from app.dashboard import dashboard
from app.models import Quiz, Topic
from app.view_helpers import daily_scores, day_names, leaderboard


def _get_user():
    return current_user if current_user.is_authenticated else None


@dashboard.route('/')
def dashboard():
    user = _get_user()

    if user:
        quiz = Quiz.query.filter_by(id=user.quiz_id).first()
        current_topic = quiz.topic
        topic_size = len(current_topic.quizzes)

        progress = current_topic.quizzes.index(quiz)
        topic_progress = "%s" % (float(progress) / topic_size * 100)
        topics = Topic.query.filter_by().all()

        return render_template(
            'dashboard/dashboard.html',
            title="LudoLatin - Dashboard",
            topic_progress=topic_progress,
            day_names=day_names(),
            daily_scores=daily_scores(),
            topics=topics,
            current_topic=current_topic,
            topic_size=topic_size,
            progress=progress,
            leaderboard=leaderboard(),
        )
    else:
        return render_template(
            'dashboard/index.html',
            title="LudoLatin: Learn Latin for free")
