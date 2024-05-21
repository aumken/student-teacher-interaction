CATEGORY=$1
news_articles=("business" "entertainment" "oddities" "politics" "science" "sports" "us-news" "world-news")
academic_papers=("cs" "econ" "eess" "math" "physics" "q-bio" "q-fin" "stat")

if [ "$CATEGORY" == "news_articles" ]; then
    for SUBCAT in "${news_articles[@]}"
    do
        #echo -e "$CATEGORY/$SUBCAT"
        python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --context-folder data/a_files/$CATEGORY/$SUBCAT --root-folder /ssd-playpen/kzaman/student-teacher-interaction --output-folder results_dynamic_plain/$CATEGORY/$SUBCAT --questions-folder data/b_questions/$CATEGORY/$SUBCAT --answers-folder data/c_answers/$CATEGORY/$SUBCAT --static-folder data/d_static/$CATEGORY/$SUBCAT #--results-folder results_dynamic_plain/$CATEGORY/$SUBCAT
    done
elif [ "$CATEGORY" == "academic_papers" ]; then
    for SUBCAT in "${academic_papers[@]}"
    do
        #echo -e "$CATEGORY/$SUBCAT"
        python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --context-folder data/a_files/$CATEGORY/$SUBCAT --root-folder /ssd-playpen/kzaman/student-teacher-interaction --output-folder results_dynamic_plain/$CATEGORY/$SUBCAT --questions-folder data/b_questions/$CATEGORY/$SUBCAT --answers-folder data/c_answers/$CATEGORY/$SUBCAT --static-folder data/d_static/$CATEGORY/$SUBCAT #--results-folder results_dynamic_plain/$CATEGORY/$SUBCAT
    done
else
    #echo "$CATEGORY"
    python 5-Dynamic/dynamic.py --context $CATEGORY --num-turns 5 --context-folder data/a_files/$CATEGORY --root-folder /ssd-playpen/kzaman/student-teacher-interaction --output-folder results_dynamic_plain/$CATEGORY --questions-folder data/b_questions/$CATEGORY --answers-folder data/c_answers/$CATEGORY --static-folder data/d_static/$CATEGORY #--results-folder results_dynamic_plain/$CATEGORY/
fi



