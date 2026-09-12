#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace JiangchengUniversity.EditorTools
{
    public static class StageAProjectConfigurator
    {
        public const string BundleIdentifier = "com.clxmhcs.University3D";
        public const string MinimumIOSVersion = "17.0";
        private const string SettingsFolder = "Assets/_Project/Settings";
        private const string PipelineAssetPath = SettingsFolder + "/JCU_URP.asset";

        [MenuItem("JCU/Stage A1/Configure Project")]
        public static void Configure()
        {
            Directory.CreateDirectory(SettingsFolder);

            EditorSettings.serializationMode = SerializationMode.ForceText;
            PlayerSettings.companyName = "clxmhcs";
            PlayerSettings.productName = "江城大学";
            PlayerSettings.SetApplicationIdentifier(BuildTargetGroup.iOS, BundleIdentifier);
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);
            PlayerSettings.iOS.targetOSVersionString = MinimumIOSVersion;
            PlayerSettings.iOS.sdkVersion = iOSSdkVersion.DeviceSDK;
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.iOS, false);
            PlayerSettings.SetGraphicsAPIs(BuildTarget.iOS, new[] { GraphicsDeviceType.Metal });

            EnsureURPAsset();

            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.iOS)
            {
                EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.iOS, BuildTarget.iOS);
            }

            AssetDatabase.SaveAssets();
            Debug.Log("[Stage A1] Project configured for iOS / Metal / IL2CPP / URP.");
        }

        private static void EnsureURPAsset()
        {
            var asset = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(PipelineAssetPath);
            if (asset == null)
            {
                asset = ScriptableObject.CreateInstance<UniversalRenderPipelineAsset>();
                AssetDatabase.CreateAsset(asset, PipelineAssetPath);
                var rendererData = asset.LoadBuiltinRendererData(RendererType.UniversalRenderer);
                if (rendererData != null)
                {
                    rendererData.name = "JCU_UniversalRenderer";
                    AssetDatabase.AddObjectToAsset(rendererData, asset);
                }
            }

            asset.supportsHDR = false;
            asset.shadowDistance = 60f;
            GraphicsSettings.defaultRenderPipeline = asset;
            QualitySettings.renderPipeline = asset;
            EditorUtility.SetDirty(asset);
        }
    }
}
#endif
