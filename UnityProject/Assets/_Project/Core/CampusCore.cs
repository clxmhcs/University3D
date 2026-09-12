using UnityEngine;

namespace JiangchengUniversity.Core
{
    public sealed class CampusCore : MonoBehaviour
    {
        public const string CampusID = "CAMPUS-01";

        private void Awake()
        {
            DontDestroyOnLoad(gameObject);
            Debug.Log("[Stage A] CampusCore initialized.");
        }
    }
}
