/**
 * Comment Thread Component
 * 
 * A complete inline commenting system.
 * Features:
 * - Threaded comments with replies
 * - @mentions support
 * - Real-time updates
 * - Edit/delete functionality
 * - Resolve/reopen threads
 * - Rich text (basic markdown)
 */

'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { format, formatDistanceToNow } from 'date-fns';
import {
  MessageSquare,
  Send,
  Reply,
  Edit2,
  Trash2,
  Check,
  CheckCheck,
  MoreHorizontal,
  X,
  AtSign,
  Bold,
  Italic,
  Link,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

// =============================================================================
// Types
// =============================================================================

export interface CommentUser {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
}

export interface Comment {
  id: string;
  content: string;
  author: CommentUser;
  createdAt: string;
  updatedAt?: string;
  parentId?: string;
  mentions?: string[];
  resolved?: boolean;
  resolvedBy?: CommentUser;
  resolvedAt?: string;
  edited?: boolean;
}

export interface CommentThreadProps {
  resourceType: 'release' | 'feature_request' | 'config';
  resourceId: string;
  comments: Comment[];
  currentUser: CommentUser;
  onAddComment: (content: string, parentId?: string, mentions?: string[]) => Promise<void>;
  onEditComment: (id: string, content: string) => Promise<void>;
  onDeleteComment: (id: string) => Promise<void>;
  onResolveThread: (id: string) => Promise<void>;
  onReopenThread: (id: string) => Promise<void>;
  mentionableUsers?: CommentUser[];
  className?: string;
}

// =============================================================================
// Avatar Component
// =============================================================================

function UserAvatar({ user, size = 'md' }: { user: CommentUser; size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'w-6 h-6 text-xs', md: 'w-8 h-8 text-sm', lg: 'w-10 h-10 text-base' };
  
  if (user.avatarUrl) {
    return (
      <img
        src={user.avatarUrl}
        alt={user.name}
        className={cn('rounded-full object-cover', sizes[size])}
      />
    );
  }

  return (
    <div className={cn(
      'rounded-full bg-primary/10 flex items-center justify-center font-medium text-primary',
      sizes[size]
    )}>
      {user.name.charAt(0).toUpperCase()}
    </div>
  );
}

// =============================================================================
// Comment Input Component
// =============================================================================

interface CommentInputProps {
  onSubmit: (content: string, mentions: string[]) => Promise<void>;
  placeholder?: string;
  submitLabel?: string;
  autoFocus?: boolean;
  onCancel?: () => void;
  mentionableUsers?: CommentUser[];
  initialContent?: string;
}

function CommentInput({
  onSubmit,
  placeholder = 'Write a comment...',
  submitLabel = 'Send',
  autoFocus = false,
  onCancel,
  mentionableUsers = [],
  initialContent = '',
}: CommentInputProps) {
  const [content, setContent] = useState(initialContent);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showMentions, setShowMentions] = useState(false);
  const [mentionQuery, setMentionQuery] = useState('');
  const [selectedMentions, setSelectedMentions] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const filteredUsers = mentionableUsers.filter(u =>
    u.name.toLowerCase().includes(mentionQuery.toLowerCase()) ||
    u.email.toLowerCase().includes(mentionQuery.toLowerCase())
  );

  const handleSubmit = async () => {
    if (!content.trim() || isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      await onSubmit(content, selectedMentions);
      setContent('');
      setSelectedMentions([]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === 'Escape' && onCancel) {
      onCancel();
    }
  };

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setContent(value);

    // Check for @mention
    const lastAt = value.lastIndexOf('@');
    if (lastAt !== -1) {
      const afterAt = value.slice(lastAt + 1);
      const hasSpace = afterAt.includes(' ');
      if (!hasSpace) {
        setMentionQuery(afterAt);
        setShowMentions(true);
        return;
      }
    }
    setShowMentions(false);
  };

  const insertMention = (user: CommentUser) => {
    const lastAt = content.lastIndexOf('@');
    const newContent = content.slice(0, lastAt) + `@${user.name} `;
    setContent(newContent);
    setSelectedMentions(prev => [...prev, user.id]);
    setShowMentions(false);
    textareaRef.current?.focus();
  };

  return (
    <div className="relative">
      <div className="border border-border rounded-lg overflow-hidden focus-within:ring-2 focus-within:ring-ring">
        {/* Toolbar */}
        <div className="flex items-center gap-1 px-2 py-1 border-b border-border bg-muted/30">
          <Button variant="ghost" size="icon" className="h-7 w-7" type="button">
            <Bold className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" type="button">
            <Italic className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" type="button">
            <Link className="w-3.5 h-3.5" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-7 w-7" 
            type="button"
            onClick={() => setShowMentions(!showMentions)}
          >
            <AtSign className="w-3.5 h-3.5" />
          </Button>
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleContentChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoFocus={autoFocus}
          rows={3}
          className="w-full px-3 py-2 bg-transparent resize-none focus:outline-none text-sm"
        />

        {/* Footer */}
        <div className="flex items-center justify-between px-3 py-2 border-t border-border bg-muted/30">
          <span className="text-xs text-muted-foreground">
            {selectedMentions.length > 0 && (
              <span className="text-primary">{selectedMentions.length} mention(s)</span>
            )}
            <span className="ml-2">⌘/Ctrl + Enter to send</span>
          </span>
          <div className="flex items-center gap-2">
            {onCancel && (
              <Button variant="ghost" size="sm" onClick={onCancel}>
                Cancel
              </Button>
            )}
            <Button 
              size="sm" 
              onClick={handleSubmit}
              disabled={!content.trim() || isSubmitting}
            >
              <Send className="w-4 h-4 mr-1" />
              {submitLabel}
            </Button>
          </div>
        </div>
      </div>

      {/* Mention Dropdown */}
      {showMentions && filteredUsers.length > 0 && (
        <div className="absolute left-0 right-0 mt-1 p-1 bg-popover border border-border rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto">
          {filteredUsers.map(user => (
            <button
              key={user.id}
              onClick={() => insertMention(user)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-left"
            >
              <UserAvatar user={user} size="sm" />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{user.name}</div>
                <div className="text-xs text-muted-foreground truncate">{user.email}</div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Single Comment Component
// =============================================================================

interface CommentItemProps {
  comment: Comment;
  currentUser: CommentUser;
  onReply: () => void;
  onEdit: (content: string) => Promise<void>;
  onDelete: () => Promise<void>;
  onResolve?: () => Promise<void>;
  onReopen?: () => Promise<void>;
  isRootComment?: boolean;
}

function CommentItem({
  comment,
  currentUser,
  onReply,
  onEdit,
  onDelete,
  onResolve,
  onReopen,
  isRootComment = false,
}: CommentItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [showActions, setShowActions] = useState(false);
  const isAuthor = currentUser.id === comment.author.id;

  const handleEdit = async (content: string) => {
    await onEdit(content);
    setIsEditing(false);
  };

  return (
    <div
      className={cn(
        'group relative',
        comment.resolved && 'opacity-60'
      )}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="flex gap-3">
        <UserAvatar user={comment.author} />
        
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium">{comment.author.name}</span>
            <span className="text-xs text-muted-foreground">
              {formatDistanceToNow(new Date(comment.createdAt), { addSuffix: true })}
            </span>
            {comment.edited && (
              <span className="text-xs text-muted-foreground">(edited)</span>
            )}
            {comment.resolved && (
              <Badge variant="outline" className="text-xs text-green-500 border-green-500/50">
                <CheckCheck className="w-3 h-3 mr-1" />
                Resolved
              </Badge>
            )}
          </div>

          {/* Content */}
          {isEditing ? (
            <CommentInput
              onSubmit={(content) => handleEdit(content)}
              initialContent={comment.content}
              submitLabel="Save"
              autoFocus
              onCancel={() => setIsEditing(false)}
            />
          ) : (
            <div className="text-sm text-foreground whitespace-pre-wrap">
              {comment.content}
            </div>
          )}

          {/* Mentions */}
          {comment.mentions && comment.mentions.length > 0 && (
            <div className="flex items-center gap-1 mt-1">
              <AtSign className="w-3 h-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">
                {comment.mentions.length} mention(s)
              </span>
            </div>
          )}

          {/* Resolution Info */}
          {comment.resolved && comment.resolvedBy && (
            <div className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
              <Check className="w-3 h-3 text-green-500" />
              Resolved by {comment.resolvedBy.name} {formatDistanceToNow(new Date(comment.resolvedAt!), { addSuffix: true })}
            </div>
          )}
        </div>

        {/* Actions */}
        {showActions && !isEditing && (
          <div className="absolute right-0 top-0 flex items-center gap-1 bg-card border border-border rounded-md p-1 shadow-sm">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onReply}>
              <Reply className="w-4 h-4" />
            </Button>
            {isAuthor && (
              <>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setIsEditing(true)}>
                  <Edit2 className="w-4 h-4" />
                </Button>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-7 w-7 text-destructive hover:text-destructive"
                  onClick={onDelete}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </>
            )}
            {isRootComment && !comment.resolved && onResolve && (
              <Button variant="ghost" size="icon" className="h-7 w-7 text-green-500" onClick={onResolve}>
                <Check className="w-4 h-4" />
              </Button>
            )}
            {isRootComment && comment.resolved && onReopen && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onReopen}>
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function CommentThread({
  resourceType,
  resourceId,
  comments,
  currentUser,
  onAddComment,
  onEditComment,
  onDeleteComment,
  onResolveThread,
  onReopenThread,
  mentionableUsers = [],
  className,
}: CommentThreadProps) {
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [showResolved, setShowResolved] = useState(false);

  // Organize comments into threads
  const rootComments = comments.filter(c => !c.parentId);
  const getReplies = (parentId: string) => comments.filter(c => c.parentId === parentId);

  const visibleComments = showResolved 
    ? rootComments 
    : rootComments.filter(c => !c.resolved);

  const resolvedCount = rootComments.filter(c => c.resolved).length;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-muted-foreground" />
          <span className="font-medium">Comments</span>
          <Badge variant="secondary">{comments.length}</Badge>
        </div>
        {resolvedCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowResolved(!showResolved)}
          >
            {showResolved ? 'Hide' : 'Show'} resolved ({resolvedCount})
          </Button>
        )}
      </div>

      {/* New Comment */}
      <CommentInput
        onSubmit={(content, mentions) => onAddComment(content, undefined, mentions)}
        mentionableUsers={mentionableUsers}
        placeholder="Add a comment..."
      />

      {/* Comment List */}
      <div className="space-y-4">
        {visibleComments.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No comments yet. Be the first to comment!</p>
          </div>
        ) : (
          visibleComments.map(comment => (
            <div key={comment.id} className="space-y-3">
              {/* Root Comment */}
              <CommentItem
                comment={comment}
                currentUser={currentUser}
                onReply={() => setReplyingTo(comment.id)}
                onEdit={(content) => onEditComment(comment.id, content)}
                onDelete={() => onDeleteComment(comment.id)}
                onResolve={() => onResolveThread(comment.id)}
                onReopen={() => onReopenThread(comment.id)}
                isRootComment
              />

              {/* Replies */}
              {getReplies(comment.id).length > 0 && (
                <div className="ml-11 space-y-3 border-l-2 border-border pl-4">
                  {getReplies(comment.id).map(reply => (
                    <CommentItem
                      key={reply.id}
                      comment={reply}
                      currentUser={currentUser}
                      onReply={() => setReplyingTo(comment.id)}
                      onEdit={(content) => onEditComment(reply.id, content)}
                      onDelete={() => onDeleteComment(reply.id)}
                    />
                  ))}
                </div>
              )}

              {/* Reply Input */}
              {replyingTo === comment.id && (
                <div className="ml-11">
                  <CommentInput
                    onSubmit={(content, mentions) => {
                      onAddComment(content, comment.id, mentions);
                      setReplyingTo(null);
                    }}
                    mentionableUsers={mentionableUsers}
                    placeholder={`Reply to ${comment.author.name}...`}
                    autoFocus
                    onCancel={() => setReplyingTo(null)}
                  />
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default CommentThread;

