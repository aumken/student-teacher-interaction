CATEGORY=$1
METHOD=$2
news_articles=("business" "entertainment" "oddities" "politics" "science" "sports" "us-news" "world-news")
academic_papers=("cs" "econ" "eess" "math" "physics" "q-bio" "q-fin" "stat")

if [ "$CATEGORY" == "news_articles" ]; then
    for SUBCAT in "${news_articles[@]}"
    do
        if [ "$METHOD" == "plain" ]; then
            python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --context-folder data/a_files/$CATEGORY/$SUBCAT --root-folder /ssd-playpen/kzaman/student-teacher-interaction --output-folder results/results_dynamic_${METHOD}/$CATEGORY/$SUBCAT --questions-folder data/b_questions/$CATEGORY/$SUBCAT --answers-folder data/c_answers/$CATEGORY/$SUBCAT --static-folder data/d_static/$CATEGORY/$SUBCAT
        elif [ "$METHOD" == "w_lesson" ]; then
            python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --context-folder data/a_files/$CATEGORY/$SUBCAT --root-folder /ssd-playpen/kzaman/student-teacher-interaction --provide-lesson --output-folder results/results_dynamic_${METHOD}/$CATEGORY/$SUBCAT --questions-folder data/b_questions/$CATEGORY/$SUBCAT --answers-folder data/c_answers/$CATEGORY/$SUBCAT --static-folder data/d_static/$CATEGORY/$SUBCAT
        elif [ "$METHOD" == "refinement" ]; then
            python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --refine-questions --context-folder data/a_files/$CATEGORY/$SUBCAT --root-folder /ssd-playpen/kzaman/student-teacher-interaction --output-folder results/results_dynamic_${METHOD}/$CATEGORY/$SUBCAT --questions-folder data/b_questions/$CATEGORY/$SUBCAT --answers-folder data/c_answers/$CATEGORY/$SUBCAT --static-folder data/d_static/$CATEGORY/$SUBCAT
        else
            echo "NO METHOD FOUND"
        fi
    done
elif [ "$CATEGORY" == "academic_papers" ]; then
    for SUBCAT in "${academic_papers[@]}"
    do
        if [ "$METHOD" == "plain" ]; then
            python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --context-folder data/a_files/$CATEGORY/$SUBCAT --root-folder /ssd-playpen/kzaman/student-teacher-interaction --output-folder results/results_dynamic_${METHOD}/$CATEGORY/$SUBCAT --questions-folder data/b_questions/$CATEGORY/$SUBCAT --answers-folder data/c_answers/$CATEGORY/$SUBCAT --static-folder data/d_static/$CATEGORY/$SUBCAT
        elif [ "$METHOD" == "w_lesson" ]; then
            python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --context-folder data/a_files/$CATEGORY/$SUBCAT --root-folder /ssd-playpen/kzaman/student-teacher-interaction --provide-lesson --output-folder results/results_dynamic_${METHOD}/$CATEGORY/$SUBCAT --questions-folder data/b_questions/$CATEGORY/$SUBCAT --answers-folder data/c_answers/$CATEGORY/$SUBCAT --static-folder data/d_static/$CATEGORY/$SUBCAT
        elif [ "$METHOD" == "refinement" ]; then
            python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --refine-questions --context-folder data/a_files/$CATEGORY/$SUBCAT --root-folder /ssd-playpen/kzaman/student-teacher-interaction --output-folder results/results_dynamic_${METHOD}/$CATEGORY/$SUBCAT --questions-folder data/b_questions/$CATEGORY/$SUBCAT --answers-folder data/c_answers/$CATEGORY/$SUBCAT --static-folder data/d_static/$CATEGORY/$SUBCAT
        else
            echo "NO METHOD FOUND"
        fi
    done
else
    if [ "$METHOD" == "plain" ]; then
        python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --context-folder data/a_files/$CATEGORY --root-folder /ssd-playpen/kzaman/student-teacher-interaction --output-folder results/results_dynamic_${METHOD}/$CATEGORY --questions-folder data/b_questions/$CATEGORY --answers-folder data/c_answers/$CATEGORY --static-folder data/d_static/$CATEGORY
    elif [ "$METHOD" == "w_lesson" ]; then
        python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --context-folder data/a_files/$CATEGORY --root-folder /ssd-playpen/kzaman/student-teacher-interaction --provide-lesson --output-folder results/results_dynamic_${METHOD}/$CATEGORY --questions-folder data/b_questions/$CATEGORY --answers-folder data/c_answers/$CATEGORY --static-folder data/d_static/$CATEGORY
    elif [ "$METHOD" == "refinement" ]; then
        python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --refine-questions --context-folder data/a_files/$CATEGORY --root-folder /ssd-playpen/kzaman/student-teacher-interaction --output-folder results/results_dynamic_${METHOD}/$CATEGORY --questions-folder data/b_questions/$CATEGORY --answers-folder data/c_answers/$CATEGORY --static-folder data/d_static/$CATEGORY
    else
        echo "NO METHOD FOUND"
    fi
fi



