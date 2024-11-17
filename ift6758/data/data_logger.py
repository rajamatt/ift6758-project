import wandb
import os

class DataLogger:
    def __init__(self, project_name,API_KEY,entity=None,group=None):
        """
        Initialize the DataLogger with the project name and optional entity.
        
        :param project_name: Name of the wandb project
        :param entity: team name or username on wandb
        """
        self.project_name = project_name
        self.entity = entity
        self.group = group
        self.dir = os.getenv('WANDB_DIR')
        os.makedirs(self.dir, exist_ok=True)
        wandb.login(key=API_KEY)
        

    def log_models(self, models):
        """
        Log multiple saved models to wandb.
        
        :param models: A list of tuples, where each tuple contains the model path and model name
        """
        run = wandb.init(project=self.project_name, 
                         dir=self.dir,
                         entity=self.entity,
                         group=self.group,
                         job_type='log_models',
                         name=f'log_models: {self.group}'
                         )
        try:
            for model_path, model_name in models:
                run.log_model(path=model_path, name=model_name)
        except Exception as e:
            print(f"Error while logging models: {e}")
            run.finish()
        run.finish()

    def log_figures(self, figures):
        """
        Log multiple matplotlib figures to wandb.
        
        :param figures: A list of tuples, where each tuple contains the figure object and figure name
        """
        run = wandb.init(project=self.project_name,
                         dir=self.dir,entity=self.entity,
                         group=self.group,
                         job_type='log_figures',
                         name=f'log_figures: {self.group}')
        try:
            for fig, fig_name in figures:
                run.log({fig_name: wandb.Image(fig)})
        except Exception as e:
            print(f"Error while logging figures: {e}")
            run.finish()
        run.finish()

