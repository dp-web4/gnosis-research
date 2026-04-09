#!/usr/bin/env python3
"""
Thor Session #72: Episode Taxonomy via Clustering

Analyze 225 learning episodes from Session #71 to discover whether there are
distinct "types" of learning episodes based on their characteristics.

Features for clustering:
- Duration (number of interaction steps)
- Amplitude (peak_c - start_c)
- Peak coherence value
- Relaxation quality (how well it returns to equilibrium)
- Rise rate (amplitude / duration_to_peak)
- Fall rate (amplitude / duration_from_peak)
"""

import json
import numpy as np
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from pathlib import Path

# Golden ratio constant
PHI = (1 + np.sqrt(5)) / 2
PHI_MINUS_1 = PHI - 1  # ≈ 0.618

def load_episodes():
    """Load all episodes from Session #71 results."""
    with open('thor_session_71_dynamics_results.json', 'r') as f:
        data = json.load(f)

    all_episodes = []
    for instance_name, instance_data in data.items():
        episodes = instance_data['learning_episodes']
        for ep in episodes:
            ep['instance'] = instance_name
            all_episodes.append(ep)

    print(f"Loaded {len(all_episodes)} episodes from {len(data)} instances")
    return all_episodes

def extract_features(episodes):
    """Extract feature vectors for clustering."""
    features = []
    feature_names = [
        'duration',
        'amplitude',
        'peak_c',
        'relaxation_quality',
        'rise_rate',
        'fall_rate',
        'dist_from_phi'
    ]

    for ep in episodes:
        duration = ep['duration']
        amplitude = ep['amplitude']
        peak_c = ep['peak_c']
        start_c = ep['start_c']
        end_c = ep['end_c']

        # Duration to peak and from peak
        duration_to_peak = ep['peak_idx'] - ep['start_idx']
        duration_from_peak = ep['end_idx'] - ep['peak_idx']

        # Relaxation quality: how close end_c is to start_c (return to equilibrium)
        relaxation_quality = 1.0 - abs(end_c - start_c) / (amplitude + 1e-6)

        # Rise and fall rates
        rise_rate = amplitude / (duration_to_peak + 1e-6)
        fall_rate = amplitude / (duration_from_peak + 1e-6)

        # Distance from golden ratio at peak
        dist_from_phi = abs(peak_c - PHI_MINUS_1)

        features.append([
            duration,
            amplitude,
            peak_c,
            relaxation_quality,
            rise_rate,
            fall_rate,
            dist_from_phi
        ])

    return np.array(features), feature_names

def find_optimal_clusters(X, max_k=10):
    """Use silhouette and elbow methods to find optimal number of clusters."""
    silhouette_scores = []
    db_scores = []
    inertias = []

    for k in range(2, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        silhouette_scores.append(silhouette_score(X, labels))
        db_scores.append(davies_bouldin_score(X, labels))
        inertias.append(kmeans.inertia_)

    # Find optimal k (max silhouette)
    optimal_k = np.argmax(silhouette_scores) + 2

    print("\nCluster quality metrics:")
    print("K\tSilhouette\tDavies-Bouldin\tInertia")
    for i, k in enumerate(range(2, max_k + 1)):
        print(f"{k}\t{silhouette_scores[i]:.3f}\t\t{db_scores[i]:.3f}\t\t{inertias[i]:.1f}")

    print(f"\nOptimal K (max silhouette): {optimal_k}")
    return optimal_k, silhouette_scores, db_scores, inertias

def cluster_episodes(X, n_clusters):
    """Perform K-means clustering."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    centroids = kmeans.cluster_centers_

    return labels, centroids

def analyze_clusters(episodes, labels, centroids, feature_names, X_scaled):
    """Analyze characteristics of each cluster."""
    scaler = StandardScaler()
    scaler.fit(X_scaled)  # Fit on scaled data to get inverse transform params

    n_clusters = len(np.unique(labels))
    cluster_stats = []

    print("\n" + "="*80)
    print("CLUSTER ANALYSIS")
    print("="*80)

    for cluster_id in range(n_clusters):
        cluster_episodes = [ep for i, ep in enumerate(episodes) if labels[i] == cluster_id]
        cluster_features = X_scaled[labels == cluster_id]

        n_episodes = len(cluster_episodes)
        pct = 100 * n_episodes / len(episodes)

        # Instance distribution
        instance_counts = {}
        for ep in cluster_episodes:
            inst = ep['instance']
            instance_counts[inst] = instance_counts.get(inst, 0) + 1

        # Mean characteristics (unscaled)
        durations = [ep['duration'] for ep in cluster_episodes]
        amplitudes = [ep['amplitude'] for ep in cluster_episodes]
        peak_cs = [ep['peak_c'] for ep in cluster_episodes]

        stats = {
            'cluster_id': cluster_id,
            'n_episodes': n_episodes,
            'pct': pct,
            'mean_duration': np.mean(durations),
            'std_duration': np.std(durations),
            'mean_amplitude': np.mean(amplitudes),
            'std_amplitude': np.std(amplitudes),
            'mean_peak_c': np.mean(peak_cs),
            'std_peak_c': np.std(peak_cs),
            'instance_distribution': instance_counts,
            'centroid': centroids[cluster_id].tolist()
        }

        cluster_stats.append(stats)

        print(f"\n--- Cluster {cluster_id} ({n_episodes} episodes, {pct:.1f}%) ---")
        print(f"Duration: {stats['mean_duration']:.1f} ± {stats['std_duration']:.1f} steps")
        print(f"Amplitude: {stats['mean_amplitude']:.3f} ± {stats['std_amplitude']:.3f}")
        print(f"Peak C: {stats['mean_peak_c']:.3f} ± {stats['std_peak_c']:.3f}")
        print(f"Instance distribution:")
        for inst, count in sorted(instance_counts.items()):
            print(f"  {inst}: {count} ({100*count/n_episodes:.1f}%)")

    return cluster_stats

def characterize_episode_types(cluster_stats):
    """Give interpretive labels to discovered episode types."""
    print("\n" + "="*80)
    print("EPISODE TYPE CHARACTERIZATION")
    print("="*80)

    # Sort by mean amplitude
    sorted_clusters = sorted(cluster_stats, key=lambda x: x['mean_amplitude'])

    type_labels = []

    for stats in sorted_clusters:
        duration = stats['mean_duration']
        amplitude = stats['mean_amplitude']
        peak_c = stats['mean_peak_c']

        # Characterization heuristics
        if amplitude < 0.10:
            intensity = "Micro"
        elif amplitude < 0.15:
            intensity = "Minor"
        elif amplitude < 0.20:
            intensity = "Moderate"
        else:
            intensity = "Major"

        if duration < 6:
            speed = "Rapid"
        elif duration < 10:
            speed = "Normal"
        else:
            speed = "Sustained"

        if peak_c < 0.70:
            level = "Low-C"
        elif peak_c < 0.75:
            level = "Mid-C"
        else:
            level = "High-C"

        label = f"{intensity} {speed} {level}"
        type_labels.append(label)

        print(f"\nCluster {stats['cluster_id']}: {label}")
        print(f"  Signature: Δ={amplitude:.3f}, τ={duration:.1f}, C_peak={peak_c:.3f}")
        print(f"  Interpretation: ", end="")

        if "Micro" in label:
            print("Fine-tuning adjustments, minimal integration load")
        elif "Minor" in label:
            print("Routine learning, standard ATP surge")
        elif "Moderate" in label:
            print("Significant integration, elevated metabolic demand")
        elif "Major" in label:
            print("Deep restructuring, maximum ATP production")

        print(f"  Prevalence: {stats['pct']:.1f}% of episodes")

    return type_labels

def main():
    """Main analysis pipeline."""
    print("Thor Session #72: Episode Taxonomy via Clustering")
    print("="*80)

    # Load data
    episodes = load_episodes()

    # Extract features
    X, feature_names = extract_features(episodes)
    print(f"\nExtracted {len(feature_names)} features: {feature_names}")

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Find optimal number of clusters
    print("\nSearching for optimal number of clusters...")
    optimal_k, sil_scores, db_scores, inertias = find_optimal_clusters(X_scaled, max_k=8)

    # Cluster with optimal K
    print(f"\nClustering with K={optimal_k}...")
    labels, centroids = cluster_episodes(X_scaled, optimal_k)

    # Analyze clusters
    cluster_stats = analyze_clusters(episodes, labels, centroids, feature_names, X_scaled)

    # Characterize episode types
    type_labels = characterize_episode_types(cluster_stats)

    # Save results (convert numpy types to native Python)
    results = {
        'n_episodes': int(len(episodes)),
        'n_clusters': int(optimal_k),
        'feature_names': feature_names,
        'cluster_stats': [
            {k: (int(v) if isinstance(v, (np.integer, np.int64)) else
                 float(v) if isinstance(v, (np.floating, np.float64)) else
                 v) for k, v in stats.items()}
            for stats in cluster_stats
        ],
        'type_labels': type_labels,
        'silhouette_scores': [float(s) for s in sil_scores],
        'davies_bouldin_scores': [float(s) for s in db_scores],
        'episodes_with_labels': [
            {**ep, 'cluster_id': int(labels[i]), 'type_label': type_labels[labels[i]]}
            for i, ep in enumerate(episodes)
        ]
    }

    with open('thor_session_72_taxonomy_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*80)
    print(f"Results saved to thor_session_72_taxonomy_results.json")
    print("="*80)

    return results

if __name__ == '__main__':
    results = main()
