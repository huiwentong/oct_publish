import traceback
import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.utils as maya_utils
from qtpy import QtCore

class MeshIntersectionRunner(object):
    """
    Mesh 穿插检查。

    示例：

        runner = MeshIntersectionRunner(
            face_chunk_size=100,
            intersection_threshold=0.2,
            ray_start_offset=0.001
        )

        bad_vertices = runner.run(meshes)

    run() 可以从 Maya 主线程或子线程调用。
    """

    def __init__(
        self,
        face_chunk_size=100,
        intersection_threshold=0.2,
        ray_start_offset=0.001,
        show_progress=True,
        progress_title=u"模型穿插检查"
    ):
        self.face_chunk_size = max(1, int(face_chunk_size))
        self.intersection_threshold = float(intersection_threshold)
        self.ray_start_offset = float(ray_start_offset)
        self.show_progress = bool(show_progress)
        self.progress_title = progress_title

    # ----------------------------------------------------------------------
    # Mesh
    # ----------------------------------------------------------------------

    @staticmethod
    def _get_mesh_path(mesh):
        """
        Transform / Mesh -> Mesh MDagPath
        """
        selection = om.MSelectionList()
        selection.add(mesh)

        dag = selection.getDagPath(0)

        if dag.apiType() == om.MFn.kTransform:
            dag.extendToShape()

        if dag.apiType() != om.MFn.kMesh:
            raise RuntimeError(
                u"节点不是有效的 Mesh：{}".format(mesh)
            )

        return dag

    @staticmethod
    def _unique_meshes(meshes):
        """
        去重，同时保持顺序。
        """
        result = []
        seen = set()

        for mesh in meshes or []:
            if not mesh:
                continue

            mesh = str(mesh)

            if mesh in seen:
                continue

            seen.add(mesh)
            result.append(mesh)

        return result

    def _build_jobs(self, meshes):
        """
        创建 Mesh 任务，并统计总面数。
        """
        jobs = []
        total_faces = 0

        for mesh in meshes:
            dag = self._get_mesh_path(mesh)
            fn = om.MFnMesh(dag)

            face_count = int(fn.numPolygons)

            if face_count <= 0:
                continue

            jobs.append(
                (
                    dag.fullPathName(),
                    face_count
                )
            )

            total_faces += face_count

        return jobs, total_faces

    # ----------------------------------------------------------------------
    # Mesh Context
    # ----------------------------------------------------------------------

    def _create_context(self, mesh):
        """
        当前 Mesh 所需的数据只创建一次。
        """
        dag = self._get_mesh_path(mesh)
        fn = om.MFnMesh(dag)

        counts, indices = fn.getVertices()

        return {
            "mesh": dag.fullPathName(),
            "fn": fn,
            "points": fn.getPoints(om.MSpace.kWorld),
            "counts": counts,
            "indices": indices,
            "accel": fn.autoUniformGridParams(),

            "face_count": int(fn.numPolygons),
            "face": 0,
            "index_offset": 0,
        }

    @staticmethod
    def _release_context(context):
        """
        释放 closestIntersection 加速缓存。
        """
        if not context:
            return

        try:
            context["fn"].freeCachedIntersectionAccelerator()
        except Exception:
            pass

    # ----------------------------------------------------------------------
    # Intersection
    # ----------------------------------------------------------------------

    def _process_chunk(self, context):
        """
        处理当前 Mesh 的一批 Face。
        """
        fn = context["fn"]
        points = context["points"]
        counts = context["counts"]
        indices = context["indices"]
        accel = context["accel"]

        mesh = context["mesh"]
        face_count = context["face_count"]

        start = context["face"]
        end = min(
            start + self.face_chunk_size,
            face_count
        )

        offset = context["index_offset"]
        bad_vertices = set()

        for face_id in range(start, end):

            count = int(counts[face_id])

            face_vertices = [
                int(indices[i])
                for i in range(offset, offset + count)
            ]

            offset += count

            # 退化面
            if count < 3:
                continue

            # --------------------------------------------------------------
            # Face 顶点平均中心
            # --------------------------------------------------------------

            x = 0.0
            y = 0.0
            z = 0.0

            for vertex_id in face_vertices:
                point = points[vertex_id]

                x += point.x
                y += point.y
                z += point.z

            inv = 1.0 / count

            center = om.MPoint(
                x * inv,
                y * inv,
                z * inv
            )

            # --------------------------------------------------------------
            # Face 世界空间法线
            # --------------------------------------------------------------

            normal = fn.getPolygonNormal(
                face_id,
                om.MSpace.kWorld
            )

            if normal.length() < 1e-12:
                continue

            # --------------------------------------------------------------
            # Ray
            # --------------------------------------------------------------

            source = om.MFloatPoint(
                center.x + normal.x * self.ray_start_offset,
                center.y + normal.y * self.ray_start_offset,
                center.z + normal.z * self.ray_start_offset
            )

            direction = om.MFloatVector(
                normal.x,
                normal.y,
                normal.z
            )

            hit = fn.closestIntersection(
                source,
                direction,
                om.MSpace.kWorld,
                self.intersection_threshold,
                False,
                accelParams=accel
            )

            # hit[2] = Face ID
            if hit and int(hit[2]) != face_id:

                for vertex_id in face_vertices:
                    bad_vertices.add(
                        "{}.vtx[{}]".format(
                            mesh,
                            vertex_id
                        )
                    )

        context["face"] = end
        context["index_offset"] = offset

        return bad_vertices, end - start

    # ----------------------------------------------------------------------
    # Progress
    # ----------------------------------------------------------------------

    def _open_progress(self, total_faces):
        if not self.show_progress:
            return False

        self._close_progress()

        try:
            cmds.progressWindow(
                title=self.progress_title,
                minValue=0,
                maxValue=max(1, total_faces),
                progress=0,
                status=u"准备检查...",
                isInterruptable=False
            )

            return True

        except Exception:
            return False

    @staticmethod
    def _close_progress():
        try:
            cmds.progressWindow(
                endProgress=True
            )
        except Exception:
            pass

    def _update_progress(self, state, context):
        if not self.show_progress:
            return

        try:
            cmds.progressWindow(
                edit=True,
                progress=min(
                    state["processed"],
                    state["total"]
                ),
                status=(
                    u"正在检查：{}\n"
                    u"模型：{}/{}\n"
                    u"当前模型：{}/{} 面\n"
                    u"总进度：{}/{} 面"
                ).format(
                    context["mesh"],
                    state["job"] + 1,
                    len(state["jobs"]),
                    context["face"],
                    context["face_count"],
                    state["processed"],
                    state["total"]
                )
            )

        except Exception:
            pass

    # ----------------------------------------------------------------------
    # Run
    # ----------------------------------------------------------------------

    def run(self, meshes):
        """
        主线程、子线程都可以调用。

        子线程：
            自动切换到 Maya 主线程执行。

        主线程：
            直接执行并返回结果。
        """
        meshes = list(meshes or [])

        if not meshes:
            return []

        # batch 模式没有 executeInMainThreadWithResult 的 idle 机制
        if cmds.about(batch=True):
            return self._run(meshes)

        return maya_utils.executeInMainThreadWithResult(
            self._run,
            meshes
        )

    def _run(self, meshes):
        """
        实际检测逻辑。
        必须运行于 Maya 主线程。
        """

        meshes = self._unique_meshes(meshes)

        if not meshes:
            return []

        jobs, total_faces = self._build_jobs(meshes)

        if not jobs:
            return []

        state = {
            "jobs": jobs,
            "job": 0,
            "context": None,

            "processed": 0,
            "total": total_faces,

            "bad": set(),
            "error": None,
            "finished": False,
        }

        timer = None
        event_loop = None
        callback = None

        progress_opened = self._open_progress(
            total_faces
        )

        try:
            event_loop = QtCore.QEventLoop()
            timer = QtCore.QTimer()

            timer.setSingleShot(True)

            # --------------------------------------------------------------
            # Finish
            # --------------------------------------------------------------

            def finish():

                if state["finished"]:
                    return

                state["finished"] = True

                if timer:
                    timer.stop()

                if event_loop:
                    event_loop.quit()

            # --------------------------------------------------------------
            # Process
            # --------------------------------------------------------------

            def process():

                try:
                    # ------------------------------------------------------
                    # 创建 Mesh Context
                    # ------------------------------------------------------

                    if state["context"] is None:

                        if state["job"] >= len(state["jobs"]):
                            finish()
                            return

                        mesh, _ = state["jobs"][state["job"]]

                        state["context"] = self._create_context(mesh)


                    context = state["context"]

                    # ------------------------------------------------------
                    # 处理一批 Face
                    # ------------------------------------------------------

                    bad, processed = (
                        self._process_chunk(context)
                    )

                    state["bad"].update(bad)
                    state["processed"] += processed

                    self._update_progress(
                        state,
                        context
                    )

                    # ------------------------------------------------------
                    # 当前 Mesh 完成
                    # ------------------------------------------------------

                    if (
                        context["face"]
                        >= context["face_count"]
                    ):
                        self._release_context(context)

                        state["context"] = None
                        state["job"] += 1

                    # ------------------------------------------------------
                    # 全部完成
                    # ------------------------------------------------------

                    if (
                        state["context"] is None
                        and state["job"] >= len(state["jobs"])
                    ):
                        finish()
                        return

                    # 下一批
                    timer.start(0)

                except Exception:

                    state["error"] = traceback.format_exc()

                    self._release_context(
                        state["context"]
                    )

                    state["context"] = None

                    finish()

            callback = process

            timer.timeout.connect(callback)
            timer.start(0)

            # PySide2 / PySide6
            if hasattr(event_loop, "exec"):
                event_loop.exec()
            else:
                event_loop.exec_()

            if state["error"]:
                raise RuntimeError(
                    state["error"]
                )

            return sorted(state["bad"])

        finally:
            if timer:

                try:
                    timer.stop()
                except Exception:
                    pass

                if callback:
                    try:
                        timer.timeout.disconnect(
                            callback
                        )
                    except Exception:
                        pass

            self._release_context(
                state["context"]
            )

            state["context"] = None

            if progress_opened:
                self._close_progress()