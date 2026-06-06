package com.example.sdk.sample

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.RecyclerView
import com.example.sdk.databinding.FragmentSampleListBinding

/**
 * Fragment demonstrating lifecycle decoupling and resolving circular dependencies in RecyclerView Adapters.
 */
class SecureFragment : Fragment() {

    // Backing property for view binding (nullable, cleared in onDestroyView)
    private var _binding: FragmentSampleListBinding? = null
    
    // Non-nullable read-only property (only valid between onCreateView and onDestroyView)
    private val binding get() = _binding!!

    // Keep adapter property nullable to clear references to ViewHolders/Views on view destruction
    private var myAdapter: SampleAdapter? = null

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSampleListBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        myAdapter = SampleAdapter()
        binding.recyclerView.adapter = myAdapter
    }

    override fun onDestroyView() {
        // 1. Break the circular reference chain between RecyclerView, Adapter, ViewHolders, and Views
        binding.recyclerView.adapter = null
        myAdapter = null
        
        // 2. Nullify binding to release layout view tree references
        _binding = null
        
        super.onDestroyView()
    }
}

// Dummy Adapter implementation
class SampleAdapter : RecyclerView.Adapter<RecyclerView.ViewHolder>() {
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
        return object : RecyclerView.ViewHolder(View(parent.context)) {}
    }
    override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {}
    override fun getItemCount(): Int = 0
}
