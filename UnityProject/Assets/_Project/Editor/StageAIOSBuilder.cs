#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace JiangchengUniversity.EditorTools
{
    public static class StageAIOSBuilder
    {
        private const string BootstrapScene = "Assets/Scenes/Bootstrap.unity";
        private const string OutputPath = "Builds/iOS";

        [MenuItem("JCU/Stage A1/Export iOS")]
        public static void Build()
        {
            StageAProjectConfigurator.Configure();

            if (!File.Exists(BootstrapScene))
            {
                CreateStageABootstrapScene.Create();
            }

            Directory.CreateDirectory(OutputPath);

            var options = new BuildPlayerOptions
            {
                scenes = new[] { BootstrapScene },
                locationPathName = OutputPath,
                target = BuildTarget.iOS,
                options = BuildOptions.Development
            };

            var report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result != BuildResult.Succeeded)
            {
                throw new System.Exception($"Stage A1 iOS export failed: {report.summary.result}");
            }

            Debug.Log($"[Stage A1] iOS export complete: {OutputPath}");
        }
    }
}
#endif
