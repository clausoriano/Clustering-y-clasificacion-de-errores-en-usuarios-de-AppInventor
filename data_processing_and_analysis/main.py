import cat_classification_gpt_api
import clustering
import get_embeddings
import location_gpt_api
import mean_time_calculator
import sentiment_analysis
import solution_finder_gpt_api
import tags
import top

# Ejecutar la totalidad del analisis de datos.
def execute_data_analysis():
    cat_classification_gpt_api.main()
    get_embeddings.main()
    clustering.main()
    sentiment_analysis.main()
    tags.main()
    location_gpt_api.main()
    mean_time_calculator.main()
    top.main()
    solution_finder_gpt_api.main()

execute_data_analysis()