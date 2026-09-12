#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using JiangchengUniversity.Bridge;
using JiangchengUniversity.Core;
using JiangchengUniversity.Streaming;
using JiangchengUniversity.Performance;
using JiangchengUniversity.Environment;
using JiangchengUniversity.Navigation;

namespace JiangchengUniversity.EditorTools
{
    public static class CreateStageABootstrapScene
    {
        [MenuItem("JCU/Stage A/Create Bootstrap Scene")]
        public static void Create()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var systems = new GameObject("PersistentSystems");
            systems.AddComponent<CampusCore>();
            systems.AddComponent<StreamingManager>();
            systems.AddComponent<PerformanceManager>();
            systems.AddComponent<AudioManager>();
            systems.AddComponent<SeasonManager>();
            systems.AddComponent<RouteManager>();

            var bridge = new GameObject("CampusBridge");
            bridge.AddComponent<CampusBridge>();

            var lightObject = new GameObject("StageA_DirectionalLight");
            var light = lightObject.AddComponent<Light>();
            light.type = LightType.Directional;
            light.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

            var cameraObject = new GameObject("StageA_Camera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.tag = "MainCamera";
            camera.transform.position = new Vector3(6f, 5f, -8f);
            camera.transform.LookAt(Vector3.zero);

            var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.name = "TEST-01";
            cube.transform.position = Vector3.zero;

            const string path = "Assets/Scenes/Bootstrap.unity";
            EditorSceneManager.SaveScene(scene, path);
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(path, true)
            };

            Debug.Log("[Stage A] Bootstrap scene created at Assets/Scenes/Bootstrap.unity.");
        }
    }
}
#endif
