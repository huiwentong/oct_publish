from dataclasses import dataclass, field, asdict
from publish_components.core import InterFace




@dataclass
class CompInterface(InterFace):

    submit_form: dict = field(
        default_factory=lambda: {
            "dcc_file": "",
            "test": True
        }
    )


    def gui_pre_interface(self):
        pass


    def init_ui(self, parent):
        pass


    def gui_post_interface(self):
        pass



if __name__ == "__main__":
    ci = CompInterface(submit_type='Daily', input_form={'dcc_file': 'sss', 'test': 'dd'}, 
                       process_data={'task_id': 143051}, 
                       dcc_file='cmd'
                       )

    print(asdict(ci))