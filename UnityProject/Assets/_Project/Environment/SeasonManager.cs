using UnityEngine;

namespace JiangchengUniversity.Environment
{
    public sealed class SeasonManager : MonoBehaviour
    {
        private void Awake()
        {
            DontDestroyOnLoad(gameObject);
            Debug.Log("[Stage A] SeasonManager initialized.");
        }
    }
}
