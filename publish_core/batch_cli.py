import json, argparse, os
def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch Publish Tool",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
JSON 配置文件示例:

{
    "task_id": 12345,
    "dcc_file": "/path/to/test.ma",
    "version_num": "v001",
    "user": "zhangsan",
    "comment": "test publish",
    "publish_type": "Dailies",
    "publish_tag_id": 1234,
    "preview_paths": [
        "/path/to/preview.mov"
    ],
    "notify": [
        "lisi",
        "wangwu"
    ]
    "input_form": {
        "ma_file" : "/path/to/test.ma",
        "zb_file" : "/path/to/test.zb",
    }
}

publish_type 可选值:
    Dailies
    Submit
    Publish

使用示例:
    rez-env PySide2 oct_publish -- batch_cli publish.json
        """
    )

    parser.add_argument("json_file", help="Publish 参数 JSON 文件路径")

    return parser.parse_args()


def execute(args):
    from publish_core.cli import PublishCli, get_user, PublishType

    task_id = args["task_id"]
    dcc_file = args["dcc_file"]
    version_num = args["version_num"]
    publish_tag_id = args["publish_tag_id"]
    input_form = args.get('input_form', {})
    preview_paths = args.get('preview_paths', [])
    comment = args.get('comment', 'batch publish tool')
    publish_type = args.get('publish_type', '')
    if publish_type:
        assert publish_type in ["Dailies", "Submit", "Publish"], "{} is not a valid publish type !!".format(publish_type)
        publish_type = PublishType(publish_type)
    else:
        publish_type = PublishType.DAILY

    user_name = args.get('user', None)
    user = get_user(user_name)

    notify_names = args.get('notify', [])
    notify = [{'sg_dingtalk_id': get_user(name).sg_dingtalk_id } for name in notify_names]

    publish_cli = PublishCli(
        user=user,
        task_id=task_id,
        input_form=input_form,
        gui=False,
        comment=comment,
        publish_tag_id=publish_tag_id,
        dcc_file=dcc_file,
        notify=notify,
        version_num=version_num,
        publish_type=publish_type,
        preview_paths=preview_paths)

    publish_cli.log.info('cli初始化完毕')
    publish_cli.interface.run_in_cli()
    publish_cli.log.info('cli程序运行完毕！')
    if publish_cli.interface.all_complete:
        publish_cli.log.info('全部运行成功！')
        publish_cli.notify_pp()


if __name__ == "__main__":
    cli_args = parse_args()
    with open(cli_args.json_file, encoding='utf-8') as f:
        args = json.load(f)
    execute(args)
    try:
        os.remove(cli_args.json_file)
    except Exception as e:
        print("Remove json failed, Because: \n{}".format(e))